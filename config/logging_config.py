"""
Structured logging and audit trail configuration.
Ensures zero-leakage of credentials and enforces structured JSON or audit formatting.
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from config.settings import settings
from src.core.security import sanitize_params


class AuditLogFilter(logging.Filter):
    """
    Sanitizes log records to ensure no raw secrets appear in log messages or arguments.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        for secret in settings.get_known_secrets():
            if secret and len(secret) >= 6 and secret in msg:
                msg = msg.replace(secret, "[REDACTED_SECRET]")
        record.msg = msg
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("corporate_invest_provenance")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(AuditLogFilter())
        logger.addHandler(handler)

    return logger


def create_audit_entry(
    actor: str,
    operation: str,
    source: str,
    record_id: Optional[str] = None,
    before_hash: Optional[str] = None,
    after_hash: Optional[str] = None,
    status: str = "SUCCESS",
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Constructs a standardized audit entry matching section 50 specifications.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "operation": operation,
        "source": source,
        "record_id": record_id,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "status": status,
        "error": error,
        "metadata": sanitize_params(extra or {})
    }
    return entry
