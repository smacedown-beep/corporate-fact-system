"""
Security guardrails: Redaction of secrets, API key masking, and parameter hashing.
Ensures zero-leakage of API keys into logs, database, or error traces.
"""
import re
import json
import hashlib
from typing import Dict, Any, List, Optional
from src.core.exceptions import SecurityViolationError

# Sensitive parameter patterns
SENSITIVE_KEYS = {
    "api_key", "apikey", "auth", "crtfc_key", "token", 
    "secret", "password", "authorization", "key"
}


def sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a copy of params with all sensitive keys replaced by REDACTED.
    """
    sanitized = {}
    for k, v in params.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_params(v)
        else:
            sanitized[k] = v
    return sanitized


def hash_request_params(params: Dict[str, Any]) -> str:
    """
    Computes a deterministic SHA256 of the request parameters after stripping out API keys.
    This allows verifying that identical query parameters produced the response,
    without storing or compromising the secret API key.
    """
    cleaned = {
        k: v for k, v in params.items() 
        if k.lower() not in SENSITIVE_KEYS
    }
    # Deterministic JSON representation
    serialized = json.dumps(cleaned, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def mask_secret(secret: Optional[str]) -> str:
    """
    Returns a masked version of a secret (e.g. 'abc1...xyz9').
    """
    if not secret:
        return "[EMPTY]"
    if len(secret) <= 8:
        return "[REDACTED]"
    return f"{secret[:4]}...{secret[-4:]}"


def validate_no_raw_secret_in_payload(payload_str: str, known_secrets: List[str]) -> None:
    """
    Security gate: scans a serialized string (log, db payload, error) for presence of raw secrets.
    Raises SecurityViolationError if any raw secret is found.
    """
    for secret in known_secrets:
        if secret and len(secret) >= 8 and secret in payload_str:
            raise SecurityViolationError("CRITICAL: Raw secret detected in outgoing payload or log message!")
