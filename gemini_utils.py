# gemini_utils.py
"""
DEBUG VERSION: Forces Raw Output to Terminal and UI.
"""

import sys
import json
import re
import time
import itertools 

# --- Dependency Check & Import ---
try:
    from google import generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    print("✅ google-generativeai imported correctly in gemini_utils.")
except ImportError:
    print("❌ Missing dependency: Ensure google-generativeai is installed.")
    sys.exit(1)

# --- Import necessary config variables ---
try:
    from config import GEMINI_MODEL_NAME, SYSTEM_PROMPT, SYSTEM_PROMPT_SCAN, API_KEY_POOL 
except ImportError:
    print("❌ FATAL: Cannot import from config.py in gemini_utils.")
    sys.exit(1)

# --- Key Pool Management ---
if not API_KEY_POOL:
    print("❌ FATAL: API Key Pool is empty.")
    sys.exit(1)

# Global variables
KEY_ITERATOR = itertools.cycle(API_KEY_POOL)
CURRENT_KEY = next(KEY_ITERATOR)
model_client = None

# --- OVERRIDE SAFETY SETTINGS (MAX PERMISSIVE) ---
# This ensures we get an answer even if the AI thinks code is "dangerous"
DEBUG_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def get_gemini_client():
    global model_client
    if model_client is None:
        try:
            genai.configure(api_key=CURRENT_KEY)
            model_client = genai.GenerativeModel(
                model_name=GEMINI_MODEL_NAME, 
                safety_settings=DEBUG_SAFETY_SETTINGS # Use Debug Settings
            )
        except Exception as e:
            print(f"❌ Error initializing Gemini client: {e}")
            model_client = None
    return model_client

def ensure_json_structure(audit_json: dict) -> dict:
    """Heals missing keys to prevent main.py crashes."""
    if "compliance" not in audit_json or not isinstance(audit_json["compliance"], dict):
        audit_json["compliance"] = {}
    if "ai_governance" not in audit_json["compliance"]:
        audit_json["compliance"]["ai_governance"] = {"model_name": GEMINI_MODEL_NAME}
    if "security_audit" not in audit_json:
        audit_json["security_audit"] = {
            "vulnerabilities_detected": [],
            "gas_cost_estimate": "UNKNOWN", 
            "is_qbc_compliant": False
        }
    return audit_json

def parse_qubic_dual_output(response_text: str):
    """Attempts to parse, but returns RAW TEXT if it fails."""
    # 1. Strict Tags
    try:
        cpp = re.search(r'\[C\+\+ START\](.*?)\[C\+\+ END\]', response_text, re.DOTALL)
        jsn = re.search(r'\[JSON START\](.*?)\[JSON END\]', response_text, re.DOTALL)
        if cpp and jsn:
            return {
                "code": cpp.group(1).strip(), 
                "json": ensure_json_structure(json.loads(jsn.group(1).replace('```json','').replace('```','')))
            }
    except: pass

    # 2. Markdown Heuristic
    try:
        # Assume last JSON block is the audit
        json_end = response_text.rfind('}')
        if json_end != -1:
            json_start = response_text.find('{', len(response_text)//3)
            if json_start == -1: json_start = response_text.find('{')
            
            if json_start != -1:
                j_txt = response_text[json_start:json_end+1]
                audit = json.loads(j_txt)
                
                # Assume everything before JSON is code
                raw_code = response_text[:json_start].strip()
                # Clean markers
                raw_code = re.sub(r'```cpp|```c\+\+|```|\[C\+\+ START\]|\[C\+\+ END\]', '', raw_code).strip()
                
                return {"code": raw_code, "json": ensure_json_structure(audit)}
    except: pass

    # 3. DEBUG PASSTHROUGH (The "Show Me The Raw Output" Layer)
    # If we can't parse it, we return the RAW TEXT as the "Code" so you can see it in the UI.
    print("⚠️ Parsing failed. Returning RAW OUTPUT to UI.")
    return {
        "code": f"// --- RAW UNPARSED OUTPUT ---\n// The parser failed, but here is what the AI said:\n\n{response_text}",
        "json": ensure_json_structure({
            "contract_id": "DEBUG-RAW",
            "contract_type": "Debug",
            "input_prompt_summary": "Raw Output Display",
            "agent_note": "Displayed raw output for debugging."
        })
    }

def rotate_client_and_key():
    global model_client, CURRENT_KEY, KEY_ITERATOR
    try:
        CURRENT_KEY = next(KEY_ITERATOR)
        model_client = None
        print(f"🔄 Rotating API Key to: ...{CURRENT_KEY[-4:]}")
        return get_gemini_client()
    except: return None
        
def generate_code_and_audit(user_prompt: str, retries: int = 3):
    client = get_gemini_client() 
    if not client: return None

    combined_prompt = f"{SYSTEM_PROMPT}\n\nUSER REQUEST: {user_prompt}"

    for attempt in range(retries):
        try:
            print(f"\n🔮 Sending Request (Attempt {attempt+1})...")
            response = client.generate_content(combined_prompt)
            
            # --- DEBUG: PRINT RAW RESPONSE TO TERMINAL ---
            print("="*40)
            print(f"RAW AI RESPONSE ({len(response.text)} chars):")
            print(response.text)
            print("="*40)
            # ---------------------------------------------

            parsed = parse_qubic_dual_output(response.text)
            if parsed: return parsed

        except Exception as e:
            err = str(e)
            print(f"🛑 Error: {err}")
            if "429" in err or "exhausted" in err:
                if rotate_client_and_key(): continue
            time.sleep(1)
            
    return {
        "code": "// Error: AI failed to respond or was blocked.",
        "json": ensure_json_structure({"contract_id": "ERR-NO-RESPONSE"})
    }

def perform_code_scan(contract_code: str, report_language: str, retries: int = 3):
    # Same logic for scanning
    client = get_gemini_client()
    prompt = f"{SYSTEM_PROMPT_SCAN}\n\nCODE:\n{contract_code}\nLANG: {report_language}"

    for attempt in range(retries):
        try:
            response = client.generate_content(prompt)
            print(f"RAW SCAN RESPONSE:\n{response.text}") # Debug print
            
            # Try parse, else return raw
            try:
                j_start = response.text.find('{')
                j_end = response.text.rfind('}')
                if j_start != -1 and j_end != -1:
                    return ensure_json_structure(json.loads(response.text[j_start:j_end+1]))
            except: pass
            
            # Fallback for scan
            return ensure_json_structure({
                "contract_id": "RAW-SCAN-OUTPUT",
                "agent_note": f"Raw output: {response.text[:200]}..."
            })
        except Exception as e:
            print(f"Error: {e}")
            if rotate_client_and_key(): continue
            
    return ensure_json_structure({"contract_id": "ERR-SCAN-FAILED"})