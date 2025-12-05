# gemini_utils.py
"""Functions for interacting with the Google Gemini API for code generation and scanning."""

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
    # UPDATED: Import both SYSTEM_PROMPT (QGEN) and SYSTEM_PROMPT_SCAN (SCAN)
    from config import GEMINI_MODEL_NAME, SYSTEM_PROMPT, SYSTEM_PROMPT_SCAN, SAFETY_SETTINGS, API_KEY_POOL 
except ImportError:
    print("❌ FATAL: Cannot import from config.py in gemini_utils.")
    sys.exit(1)

# --- Key Pool Management ---
if not API_KEY_POOL:
    print("❌ FATAL: API Key Pool is empty. Please check your .env and config.py")
    sys.exit(1)

# Global variables for client management
KEY_ITERATOR = itertools.cycle(API_KEY_POOL)
CURRENT_KEY = next(KEY_ITERATOR)
model_client = None


def get_gemini_client():
    """Initializes and returns the global Gemini client."""
    global model_client
    if model_client is None:
        try:
            genai.configure(api_key=CURRENT_KEY)
            model_client = genai.GenerativeModel(
                model_name=GEMINI_MODEL_NAME, 
                safety_settings=SAFETY_SETTINGS
            )
            print(f"✅ Gemini client initialized with key ending in: ...{CURRENT_KEY[-4:]}")
        except Exception as e:
            print(f"❌ Error initializing Gemini client: {e}")
            model_client = None
    return model_client


def parse_qubic_dual_output(response_text: str):
    """
    Parses the dual output (C++ code and JSON audit) from the Q-Gen prompt.
    Uses strict markers: [C++ START]/[C++ END] and [JSON START]/[JSON END].
    (Used for GENERATION mode)
    """
    cpp_match = re.search(r'\[C\+\+ START\](.*?)\[C\+\+ END\]', response_text, re.DOTALL)
    json_match = re.search(r'\[JSON START\](.*?)\[JSON END\]', response_text, re.DOTALL)

    if not cpp_match or not json_match:
        # print("❌ Parsing failed: Could not find both [C++ START] and [JSON START] markers.")
        return None

    cpp_code = cpp_match.group(1).strip()
    json_text = json_match.group(1).strip()

    try:
        # Clean up JSON text (remove markdown backticks if accidentally included)
        json_text = json_text.strip().replace('```json', '').replace('```', '')
        
        audit_json = json.loads(json_text)
        return {
            "code": cpp_code,
            "json": audit_json
        }
    except json.JSONDecodeError as e:
        # print(f"❌ JSON Parsing failed: {e}")
        return None

def parse_qubic_scan_output(response_text: str):
    """
    Parses the JSON audit output from the Q-Gen SCAN prompt.
    Uses strict markers: [JSON START]/[JSON END].
    (Used for SCANNING mode)
    """
    json_match = re.search(r'\[JSON START\](.*?)\[JSON END\]', response_text, re.DOTALL)

    if not json_match:
        # print("❌ Scanning Parsing failed: Could not find [JSON START] marker.")
        return None

    json_text = json_match.group(1).strip()

    try:
        # Clean up JSON text (remove markdown backticks if accidentally included)
        json_text = json_text.strip().replace('```json', '').replace('```', '')
        
        audit_json = json.loads(json_text)
        return audit_json
    except json.JSONDecodeError as e:
        # print(f"❌ JSON Parsing failed in scanning mode: {e}")
        return None

def rotate_client_and_key():
    """Rotates to the next API key and re-initializes the global client."""
    global model_client, CURRENT_KEY, KEY_ITERATOR
    
    try:
        next_key = next(KEY_ITERATOR)
        CURRENT_KEY = next_key
        model_client = None
        return get_gemini_client()
        
    except Exception as e:
        print(f"❌ Key rotation failed: {e}")
        return None
        
        
def generate_code_and_audit(user_prompt: str, retries: int = 3):
    """
    Main function to call Gemini for Q-Gen: sends prompt and parses C++ code + JSON audit.
    (GENERATION MODE)
    """
    client = get_gemini_client() 
    if not client:
        return None

    # Combine SYSTEM_PROMPT (QGEN) and user_prompt into 'contents'
    combined_prompt = f"{SYSTEM_PROMPT}\n\nUSER REQUEST: {user_prompt}"

    for attempt in range(retries):
        try:
            # Send the combined prompt as the content.
            response = client.generate_content(
                contents=combined_prompt, 
                generation_config={"max_output_tokens": 4096}
            )
            response_text = response.text
            
            # --- Parse Output (Dual Parser) ---
            parsed = parse_qubic_dual_output(response_text)
            if parsed:
                return parsed # Success!
            else:
                # Parsing failed, wait and retry
                print(f"   Parsing failed (Attempt {attempt + 1}/{retries}). Retrying in 5s...")
                time.sleep(5)
                continue 

        except Exception as e:
            error_str = str(e)
            # --- Key Rotation Logic for Rate Limit ---
            if "Resource has been exhausted" in error_str or "429" in error_str or "rate limit" in error_str.lower():
                print(f"🚦 Rate Limit Hit (Attempt {attempt + 1}/{retries}).")
                new_client = rotate_client_and_key()
                if new_client:
                    print(f"   Retrying with new key ending in: ...{CURRENT_KEY[-4:]}")
                    continue 
                else:
                    print("   Max retries reached after key rotation failure. Skipping.")
                    return None
            # --- Standard Retry Logic ---
            elif "internal server error" in error_str.lower() or "500" in error_str or "service unavailable" in error_str.lower():
                 wait_time = 10 * (attempt + 1); print(f"🔧 API Internal/Unavailable Error (Attempt {attempt + 1}/{retries}). Retrying in {wait_time}s...")
                 time.sleep(wait_time)
            else:
                print(f"🛑 API Error (Attempt {attempt + 1}/{retries}): {e}");
                if attempt < retries - 1:
                    wait_time = 7 * (attempt + 1); print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print("   Max retries reached for general error. Skipping."); return None
            
    return None

def perform_code_scan(contract_code: str, report_language: str, retries: int = 3):
    """
    Calls Gemini for Q-Gen SCAN: sends code and language, expects translated JSON audit.
    (SCANNING MODE)
    """
    client = get_gemini_client() 
    if not client:
        return None
    
    # --- Combine Prompts for Scanning ---
    combined_prompt = (
        f"{SYSTEM_PROMPT_SCAN}\n\n"
        f"--- USER INPUT ---\n"
        f"C++ Code:\n```cpp\n{contract_code}\n```\n"
        f"REQUIRED REPORT LANGUAGE CODE: {report_language.upper()}"
    )

    for attempt in range(retries):
        try:
            response = client.generate_content(
                contents=combined_prompt, 
                generation_config={"max_output_tokens": 4096}
            )
            response_text = response.text
            
            # --- Parse Output (Scan Parser) ---
            parsed = parse_qubic_scan_output(response_text)
            if parsed:
                return parsed # Success!
            else:
                # Parsing failed, wait and retry
                print(f"   Scanning Parsing failed (Attempt {attempt + 1}/{retries}). Retrying in 5s...")
                time.sleep(5)
                continue 

        except Exception as e:
            error_str = str(e)
            # --- Key Rotation Logic for Rate Limit ---
            if "Resource has been exhausted" in error_str or "429" in error_str or "rate limit" in error_str.lower():
                print(f"🚦 Rate Limit Hit (Attempt {attempt + 1}/{retries}). Rotating Key.")
                new_client = rotate_client_and_key()
                if new_client:
                    print(f"   Retrying with new key ending in: ...{CURRENT_KEY[-4:]}")
                    continue 
                else:
                    print("   Max retries reached after key rotation failure. Skipping.")
                    return None
            
            # --- Standard Retry Logic ---
            elif "internal server error" in error_str.lower() or "500" in error_str or "service unavailable" in error_str.lower():
                 wait_time = 10 * (attempt + 1); print(f"🔧 API Internal/Unavailable Error (Attempt {attempt + 1}/{retries}). Retrying in {wait_time}s...")
                 time.sleep(wait_time)
            else:
                print(f"🛑 API Error (Attempt {attempt + 1}/{retries}): {e}");
                if attempt < retries - 1:
                    wait_time = 7 * (attempt + 1); print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print("   Max retries reached for general error. Skipping."); return None
            
    return None