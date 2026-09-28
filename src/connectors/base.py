"""
Base Connector for Official Sources.
Provides rate limiting, exponential backoff, retry handling, secret redaction,
and response preservation with dual cryptographic hashes.
"""
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from config.settings import settings, RAW_EVIDENCE_ROOT, PROJECT_ROOT
from config.rate_limits import PROVIDER_RATE_LIMITS, RateLimitConfig
from src.core.enums import SourceProvider
from src.core.hashing import compute_hashes
from src.core.security import sanitize_params, hash_request_params
from src.core.exceptions import ProvenanceSystemError, SecurityViolationError


class NonRetryableApiError(ProvenanceSystemError):
    """Raised for 401, 403, 404, or unrecoverable client errors."""
    pass


class RetryableApiError(ProvenanceSystemError):
    """Raised for 429, 500, 502, 503 errors when retries are exhausted."""
    pass


@dataclass
class AcquisitionResponse:
    http_status: int
    content: bytes
    sha256: str
    sha1: str
    size_bytes: int
    raw_storage_path: str
    request_parameters_hash: str
    acquired_at: datetime
    headers: Dict[str, str]


class BaseConnector:
    def __init__(self, provider: SourceProvider):
        self.provider = provider
        self.rate_config: RateLimitConfig = PROVIDER_RATE_LIMITS[provider]
        self._request_timestamps = []

    def _enforce_rate_limit(self):
        """Enforces sliding window rate limiting."""
        now = time.time()
        cutoff = now - self.rate_config.window_seconds
        self._request_timestamps = [t for t in self._request_timestamps if t > cutoff]

        if len(self._request_timestamps) >= self.rate_config.max_requests_per_window:
            sleep_time = self.rate_config.window_seconds - (now - self._request_timestamps[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)

        self._request_timestamps.append(time.time())

    def preserve_response(
        self,
        content: bytes,
        extension: str = "bin",
        subfolder: Optional[str] = None,
        prefix: str = "acq"
    ) -> tuple[str, Dict[str, Any]]:
        """
        Preserves raw response payload to disk immutably. Never overwrites existing files.
        """
        provider_dir = RAW_EVIDENCE_ROOT / self.provider.value.lower()
        if subfolder:
            target_dir = provider_dir / subfolder
        else:
            target_dir = provider_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        hashes = compute_hashes(content)
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{ts_str}_{hashes['sha256'][:12]}.{extension}"
        file_path = target_dir / filename

        # Ensure no overwrite
        counter = 1
        while file_path.exists():
            filename = f"{prefix}_{ts_str}_{hashes['sha256'][:12]}_{counter}.{extension}"
            file_path = target_dir / filename
            counter += 1

        file_path.write_bytes(content)
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
        return rel_path, hashes
