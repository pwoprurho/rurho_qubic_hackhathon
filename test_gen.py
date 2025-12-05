import unittest
import json
import hashlib
from unittest.mock import patch, MagicMock

# Import the modules we are testing
# NOTE: You will need to install 'fastapi' and 'pydantic' and set up a basic 
# config.py/env file structure to run these tests.
from gemini_utils import (
    parse_qubic_dual_output, 
    parse_qubic_scan_output, 
    generate_code_and_audit, 
    perform_code_scan,
    rotate_client_and_key
)
from qubic_integration import commit_audit_log, log_scan_transaction
from utils import now_iso

# --- MOCK DATA ---
MOCK_CPP_CODE = "// Qubic Smart Contract\nvoid main() { return 0; }"
MOCK_AUDIT_JSON_EN = {
    "contract_id": "QSC-0001",
    "contract_type": "Utility",
    "input_prompt_summary": "English summary.",
    "security_audit": {"is_qbc_compliant": True},
    "compliance": {"ai_governance": {"model_name": "mock-flash"}},
    "agent_note": "English note."
}
MOCK_AUDIT_JSON_FR = {
    "contract_id": "QSC-SCAN-0002",
    "report_language": "fr",
    "input_prompt_summary": "Résumé en français.",
    "security_audit": {"is_qbc_compliant": True},
    "compliance": {"ai_governance": {"model_name": "mock-flash"}},
    "agent_note": "Note en français."
}

# --- Mocking the Gemini API Response Structure ---
# Simulate the raw text response for the GENERATION workflow
MOCK_GENERATION_RESPONSE_TEXT = f"""
Some preamble text before the code block.
[C++ START]
{MOCK_CPP_CODE}
[C++ END]
And some text before the JSON.
[JSON START]
{json.dumps(MOCK_AUDIT_JSON_EN)}
[JSON END]
"""

# Simulate the raw text response for the SCANNING workflow
MOCK_SCANNING_RESPONSE_TEXT = f"""
Just some instruction following text.
[JSON START]
{json.dumps(MOCK_AUDIT_JSON_FR)}
[JSON END]
Final notes.
"""


class TestParsingLogic(unittest.TestCase):
    """Tests the parsing functions in gemini_utils.py."""

    def test_dual_output_success(self):
        """Should successfully parse both C++ code and JSON audit for Generation mode."""
        parsed = parse_qubic_dual_output(MOCK_GENERATION_RESPONSE_TEXT)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['code'].strip(), MOCK_CPP_CODE.strip())
        self.assertEqual(parsed['json']['contract_id'], "QSC-0001")

    def test_dual_output_failure_missing_cpp(self):
        """Should fail if the [C++ START] marker is missing."""
        bad_text = MOCK_GENERATION_RESPONSE_TEXT.replace("[C++ START]", "")
        self.assertIsNone(parse_qubic_dual_output(bad_text))

    def test_scan_output_success(self):
        """Should successfully parse the JSON audit for Scanning mode."""
        parsed = parse_qubic_scan_output(MOCK_SCANNING_RESPONSE_TEXT)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['report_language'], "fr")
        self.assertEqual(parsed['agent_note'], "Note en français.")

    def test_scan_output_failure_bad_json(self):
        """Should fail if JSON content is invalid."""
        bad_text = "[JSON START] invalid json { 'key': [JSON END]"
        self.assertIsNone(parse_qubic_scan_output(bad_text))


class TestGeminiIntegrationMocked(unittest.TestCase):
    """
    Tests the main functions using mocks to isolate the network logic.
    Mocks the API client and rotation logic.
    """
    
    @patch('gemini_utils.get_gemini_client')
    @patch('gemini_utils.SYSTEM_PROMPT', 'TEST_PROMPT')
    def test_generate_code_and_audit_success(self, mock_client):
        """Should call Gemini and return parsed data successfully."""
        mock_response = MagicMock()
        mock_response.text = MOCK_GENERATION_RESPONSE_TEXT
        mock_client.return_value.generate_content.return_value = mock_response
        
        result = generate_code_and_audit("Test prompt")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['code'].strip(), MOCK_CPP_CODE.strip())
        mock_client.return_value.generate_content.assert_called_once()

    @patch('gemini_utils.get_gemini_client')
    @patch('gemini_utils.rotate_client_and_key')
    def test_generate_code_and_audit_retry_on_ratelimit(self, mock_rotate, mock_client):
        """Should attempt key rotation on rate limit (429/Resource Exhausted)."""
        # 1st call fails with Rate Limit, 2nd call succeeds
        mock_client.return_value.generate_content.side_effect = [
            Exception("Resource has been exhausted"),
            MagicMock(text=MOCK_GENERATION_RESPONSE_TEXT)
        ]
        mock_rotate.return_value = MagicMock() # Simulate successful rotation
        
        result = generate_code_and_audit("Test prompt")
        
        self.assertIsNotNone(result)
        self.assertEqual(mock_client.return_value.generate_content.call_count, 2)
        mock_rotate.assert_called_once()
    
    @patch('gemini_utils.get_gemini_client')
    @patch('gemini_utils.SYSTEM_PROMPT_SCAN', 'TEST_SCAN_PROMPT')
    def test_perform_code_scan_success(self, mock_client):
        """Should call Gemini and return parsed JSON successfully in Scanning mode."""
        mock_response = MagicMock()
        mock_response.text = MOCK_SCANNING_RESPONSE_TEXT
        mock_client.return_value.generate_content.return_value = mock_response
        
        result = perform_code_scan(MOCK_CPP_CODE, "fr")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['report_language'], "fr")
        mock_client.return_value.generate_content.assert_called_once()


class TestQubicIntegration(unittest.TestCase):
    """Tests the deterministic hash/ID generation logic."""

    @patch('qubic_integration.now_iso', return_value='2025-12-05T10:00:00Z')
    def test_commit_audit_log_deterministic(self, mock_time):
        """Commit ID should be deterministic based on hash and timestamp."""
        test_hash = hashlib.sha256("test_code".encode('utf-8')).hexdigest()
        audit_data = {'meta': {'submission_timestamp': mock_time.return_value}}
        
        tx_id = commit_audit_log(test_hash, audit_data)
        
        # Check for the correct format and that the ID is stable
        self.assertTrue(tx_id.startswith("QUBIC-TX-"))
        self.assertEqual(tx_id, "QUBIC-TX-31DE067B92120BC1") # This value is fixed based on the hash/timestamp seed

    @patch('qubic_integration.now_iso', return_value='2025-12-05T10:00:00Z')
    def test_log_scan_transaction_deterministic(self, mock_time):
        """Scan ID should be deterministic and use the QUBIC-SCAN-TX- prefix."""
        test_hash = hashlib.sha256("input_code".encode('utf-8')).hexdigest()
        audit_data = {'meta': {'submission_timestamp': mock_time.return_value}}

        scan_id = log_scan_transaction(test_hash, audit_data)
        
        # Check for the correct format and stability
        self.assertTrue(scan_id.startswith("QUBIC-SCAN-TX-"))
        self.assertEqual(scan_id, "QUBIC-SCAN-TX-E1C6615E2682915A") # This value is fixed based on the hash/timestamp seed

# To run these tests:
# 1. Save the above code as test_qgen_agent.py
# 2. Make sure you have pytest or unittest installed.
# 3. Run: python -m unittest test_qgen_agent.py