# main.py
# Qubic Agent C++ Generator/Scanner (Q-Gen) API Endpoint

import time
import hashlib
import json
import sys
from typing import Union, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse  # <--- NEW IMPORT
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Import Core Logic ---
try:
    from gemini_utils import generate_code_and_audit, perform_code_scan 
    from utils import now_iso 
    from qubic_integration import commit_audit_log, log_scan_transaction
except ImportError as e:
    print(f"❌ FATAL: Could not import necessary modules: {e}")
    sys.exit(1)

# --- FastAPI Initialization ---
app = FastAPI(
    title="Qubic C++ Agent Generator/Scanner (Q-Gen) API",
    description="Generates, audits, and blockchain-verifies Qubic Smart Contract code.",
    version="1.0.0"
)

# --- Add CORS Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# === IN-MEMORY RATE LIMITER CONFIGURATION ===
# =========================================================================

REQUEST_HISTORY = {}
RATE_LIMIT_MAX_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60 

def check_rate_limit(client_ip: str):
    """
    Checks if the client IP has exceeded the allowed number of requests 
    within the defined time window.
    """
    current_time = time.time()
    
    if client_ip in REQUEST_HISTORY:
        REQUEST_HISTORY[client_ip] = [
            t for t in REQUEST_HISTORY[client_ip] 
            if t > (current_time - RATE_LIMIT_WINDOW_SECONDS)
        ]

    current_request_count = len(REQUEST_HISTORY.get(client_ip, []))
    
    if current_request_count >= RATE_LIMIT_MAX_REQUESTS:
        earliest_timestamp = REQUEST_HISTORY[client_ip][0]
        time_to_wait = earliest_timestamp + RATE_LIMIT_WINDOW_SECONDS - current_time
        
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {time_to_wait:.1f} seconds."
        )

    if client_ip not in REQUEST_HISTORY:
        REQUEST_HISTORY[client_ip] = []
    REQUEST_HISTORY[client_ip].append(current_time)


# --- Request Model ---
class QGenRequest(BaseModel):
    user_prompt: Optional[str] = Field(
        None, min_length=10, max_length=4000, 
        description="User's natural language request for code generation."
    )
    contract_code: Optional[str] = Field(
        None, min_length=50, max_length=50000, 
        description="Raw C++ code to be audited."
    )
    report_language: Optional[str] = Field(
        "en", min_length=2, max_length=2,
        description="ISO 639-1 language code for the audit report translation."
    )
    client_ref_id: Union[str, None] = "POC-HACKATHON-2025"

# =========================================================================
# === ROOT ENDPOINT (Serves the Frontend) ===
# =========================================================================
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the index.html file at the root URL."""
    try:
        # Assumes index.html is in the same directory
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: index.html not found on server.</h1>"

# =========================================================================
# === API ENDPOINT ===
# =========================================================================
@app.post("/generate")
async def process_qubic_request(request: Request, body: QGenRequest):
    start_time = time.time()

    # --- 0. RATE LIMIT CHECK ---
    client_ip = request.client.host
    # If behind a proxy (like Render), X-Forwarded-For is better, but this works for simple setup
    check_rate_limit(client_ip)
    print(f"Client IP: {client_ip} is within rate limits.")
    
    # --- Dual Mode Detection ---
    user_prompt = body.user_prompt.strip() if body.user_prompt else None
    contract_code = body.contract_code.strip() if body.contract_code else None
    
    is_generation_mode = user_prompt is not None and user_prompt != ""
    is_scanning_mode = contract_code is not None and contract_code != ""

    if not (is_generation_mode or is_scanning_mode):
        raise HTTPException(status_code=400, detail="Request must contain either 'user_prompt' or 'contract_code'.")
        
    if is_generation_mode and is_scanning_mode:
        raise HTTPException(status_code=400, detail="Request cannot contain both modes simultaneously.")

    # --- Mode: GENERATION ---
    if is_generation_mode:
        print(f"\n🚀 MODE: GENERATION. Prompt: '{user_prompt[:50]}...'")

        code_and_audit = generate_code_and_audit(user_prompt) 
        
        if not code_and_audit or 'code' not in code_and_audit or 'json' not in code_and_audit:
            raise HTTPException(status_code=500, detail="AI returned incomplete or unparsable output after retries.")

        generated_cpp_code = code_and_audit['code']
        audit_json_data = code_and_audit['json']
        
        code_hash = hashlib.sha256(generated_cpp_code.encode('utf-8')).hexdigest()
        
        audit_json_data['compliance']['ai_governance']['audit_timestamp'] = now_iso() 
        audit_json_data['meta'] = {
            "client_ref_id": body.client_ref_id,
            "generated_code_hash": code_hash,
            "mode": "GENERATION"
        }

        transaction_id = commit_audit_log(code_hash, audit_json_data) 
        
        total_duration = time.time() - start_time
        print(f"✅ Success. Code generated and committed in {total_duration:.2f}s.")

        return {
            "status": "success",
            "mode": "GENERATION",
            "generated_code": generated_cpp_code,
            "security_audit": audit_json_data,
            "qubic_transaction_id": transaction_id,
            "code_hash": code_hash,
            "duration_seconds": round(total_duration, 2)
        }

    # --- Mode: SCANNING ---
    elif is_scanning_mode:
        report_lang = body.report_language.strip()
        print(f"\n🔍 MODE: SCANNING. Code length: {len(contract_code)} chars. Language: {report_lang.upper()}")
        
        audit_json_data = perform_code_scan(contract_code, report_lang) 
        
        if not audit_json_data:
            raise HTTPException(status_code=500, detail="AI failed to produce a parsable JSON audit.")

        code_hash = hashlib.sha256(contract_code.encode('utf-8')).hexdigest()
        
        audit_json_data['compliance']['ai_governance']['audit_timestamp'] = now_iso() 
        audit_json_data['meta'] = {
            "client_ref_id": body.client_ref_id,
            "scanned_code_hash": code_hash,
            "mode": "SCANNING"
        }

        transaction_id = log_scan_transaction(code_hash, audit_json_data) 
        
        total_duration = time.time() - start_time
        print(f"✅ Success. Code scanned and committed in {total_duration:.2f}s.")

        return {
            "status": "success",
            "mode": "SCANNING",
            "security_audit": audit_json_data,
            "qubic_transaction_id": transaction_id,
            "code_hash": code_hash,
            "duration_seconds": round(total_duration, 2)
        }

    raise HTTPException(status_code=400, detail="Invalid request payload structure.")

# --- Health Check ---
@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Q-Gen API"}