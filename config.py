# config.py
"""Configuration settings and data loading for the Q-Gen Agent."""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# --- Dependency Check ---
try:
    from google import generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    print("✅ google-generativeai library and safety types imported successfully.")
except ImportError:
    print("❌ Missing dependency: Please install/upgrade `pip install --upgrade google-generativeai`")
    sys.exit(1)

# --- Base Paths ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "qgen_output"
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"📂 Output directory set to: {OUTPUT_DIR}")

# --- Load API Key Pool (NEW) ---
print("🔑 Loading API Key Pool from .env file...")
load_dotenv(BASE_DIR / ".env")

API_KEY_POOL = []
# Load all keys starting with GEMINI_API_KEY_...
for i in range(1, 10):  # Will check for keys 1 through 9
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        API_KEY_POOL.append(key)

# Fallback to the original single key if pool is empty
if not API_KEY_POOL:
    key = os.getenv("GEMINI_API_KEY") # Check for the old single key
    if key:
        API_KEY_POOL.append(key)
    else:
        # Placeholder key as per previous snippet for demonstration purposes
        API_KEY_POOL.append("AIzaSyDBTJjpYAmoJOe5aa9J3RvI10-XNtBnoIU") 

if not API_KEY_POOL:
    print("❌ FATAL: GEMINI_API_KEY missing in .env. Please check your config.")
    sys.exit(1)
print(f"🔑 API Key Pool loaded successfully. ({len(API_KEY_POOL)} key(s) available)")


# --- Q-Gen Configuration ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite" 
# --- System Prompt Files ---
SYSTEM_PROMPT_QGEN_FILE = BASE_DIR / "system_prompt_qgen.txt" 
SYSTEM_PROMPT_SCAN_FILE = BASE_DIR / "system_prompt_scan.txt" # NEW SCANNING PROMPT

NUM_PER_SCENARIO = 1 # Not used in API, but kept for compatibility
SCENARIOS = [] # Not used in API, but kept for compatibility

# Load the Q-Gen System Prompts
SYSTEM_PROMPT = ""
SYSTEM_PROMPT_SCAN = ""

def load_prompt_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        if not prompt_content.strip():
            raise ValueError(f"System prompt file '{file_path.name}' is empty.")
        print(f"📜 {file_path.name} loaded successfully.")
        return prompt_content
    except FileNotFoundError:
        print(f"❌ FATAL: System prompt file not found at '{file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ FATAL: Error loading system prompt file '{file_path.name}': {e}")
        sys.exit(1)

SYSTEM_PROMPT = load_prompt_file(SYSTEM_PROMPT_QGEN_FILE)
SYSTEM_PROMPT_SCAN = load_prompt_file(SYSTEM_PROMPT_SCAN_FILE)


# --- Safety Settings ---
from google.generativeai.types import HarmCategory, HarmBlockThreshold # Explicitly imported for clarity
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}
print("🛡️ Safety settings configured.")