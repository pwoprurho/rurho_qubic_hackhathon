# utils.py
"""Utility functions for the Q-Gen Agent."""

import uuid
from datetime import datetime, timezone

def generate_case_id(prefix="CASE"):
    """Generates a unique-ish case ID (not currently used by main.py but good practice)."""
    clean_prefix = "".join(filter(str.isalnum, prefix))[:4].upper()
    return f"{clean_prefix}-{uuid.uuid4().hex[:8].upper()}"

def now_iso():
    """Returns the current timestamp in ISO 8601 format (UTC)."""
    # Returns a string like '2025-12-04T20:30:00Z'
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')