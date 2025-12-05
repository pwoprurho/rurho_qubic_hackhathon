# qubic_integration.py
"""Mocks the Qubic SDK interaction for proof-of-concept submission."""

import time
import hashlib
import json
from utils import now_iso 

def commit_audit_log(code_hash: str, audit_data: dict) -> str:
    """
    Simulates the process of hashing the code and audit data,
    and committing a transaction to the Qubic testnet for GENERATED code.
    
    This generates a deterministic mock Tx ID: QUBIC-TX-...
    """
    print("\n--- 🔨 Simulating Qubic GENERATION Commit ---")
    
    # 1. Prepare data for the simulated commit
    immutable_seed = f"{code_hash}-{audit_data.get('meta', {}).get('submission_timestamp')}"
    
    # 2. Simulate Qubic Transaction ID generation
    transaction_id_hash = hashlib.sha256(immutable_seed.encode('utf-8')).hexdigest()
    
    # Mocking the Qubic transaction ID format
    mock_transaction_id = f"QUBIC-TX-{transaction_id_hash[:16].upper()}"
    
    print(f"✅ Audit Hash Generated: {code_hash}")
    print(f"✅ Mock Qubic Transaction ID: {mock_transaction_id}")
    print("--- Commit Simulation Complete ---\n")
    
    return mock_transaction_id

def log_scan_transaction(code_hash: str, audit_data: dict) -> str:
    """
    Simulates the process of logging an external code audit transaction.
    
    This generates a deterministic mock Tx ID: QUBIC-SCAN-TX-...
    """
    print("\n--- 🔨 Simulating Qubic SCANNING Commit ---")
    
    # 1. Prepare data for the simulated commit (using the input code's hash)
    immutable_seed = f"SCAN-{code_hash}-{audit_data.get('meta', {}).get('submission_timestamp')}"
    
    # 2. Simulate Qubic Transaction ID generation
    transaction_id_hash = hashlib.sha256(immutable_seed.encode('utf-8')).hexdigest()
    
    # Mocking the Qubic transaction ID format for scanning
    mock_transaction_id = f"QUBIC-SCAN-TX-{transaction_id_hash[:16].upper()}"
    
    print(f"✅ Input Code Hash Logged: {code_hash}")
    print(f"✅ Mock Qubic Scan Transaction ID: {mock_transaction_id}")
    print("--- Scan Log Simulation Complete ---\n")
    
    return mock_transaction_id