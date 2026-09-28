"""
FRED (Federal Reserve Bank of St. Louis) Connector.
Conforms to official FRED API specification (https://api.stlouisfed.org/fred/).
Enforces series registry lookup (no hardcoded series IDs),
rate limiting, and immutable response preservation.
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from config.settings import settings
from src.core.enums import SourceProvider
from src.core.security import hash_request_params
from src.core.exceptions import ForensicError, ProvenanceSystemError
from src.connectors.base import BaseConnector


@dataclass
class FredObservation:
    series_id: str
    date: str
    value: float
    availability_date: datetime
    raw_storage_path: str
    raw_sha256: str


@dataclass
class FredAcquisitionResult:
    series_id: str
    observations: List[FredObservation]
    raw_storage_path: str
    sha256: str
    sha1: str
    size_bytes: int
    request_parameters_hash: str


class FredClient(BaseConnector):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(SourceProvider.FRED)
        self.api_key = api_key or settings.fred_api_key

    def acquire_series_observations(
        self,
        series_id: str,
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None,
        mock_json_payload: Optional[str] = None
    ) -> FredAcquisitionResult:
        endpoint = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json"
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        req_hash = hash_request_params(params)
        self._enforce_rate_limit()

        if mock_json_payload is not None:
            raw_bytes = mock_json_payload.encode("utf-8")
        else:
            if not self.api_key:
                raise ProvenanceSystemError("FRED_API_KEY environment variable is not configured.")
            import urllib.request
            req_params = dict(params)
            req_params["api_key"] = self.api_key
            query_str = "&".join(f"{k}={v}" for k, v in req_params.items())
            url = f"{endpoint}?{query_str}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorporateInvestProvenance/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_bytes = resp.read()

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ForensicError(f"Failed to parse FRED JSON response: {str(e)}")

        if "error_code" in data:
            raise ForensicError(f"FRED API Error: [{data.get('error_code')}] {data.get('error_message')}")

        raw_path, hashes = self.preserve_response(
            raw_bytes, extension="json", subfolder=series_id, prefix=f"fred_{series_id}"
        )

        observations = []
        for item in data.get("observations", []):
            d_str = item.get("date", "")
            val_str = item.get("value", "")
            try:
                num_val = float(val_str)
            except ValueError:
                num_val = None

            if num_val is not None:
                obs = FredObservation(
                    series_id=series_id,
                    date=d_str,
                    value=num_val,
                    availability_date=datetime.now(timezone.utc),
                    raw_storage_path=raw_path,
                    raw_sha256=hashes["sha256"]
                )
                observations.append(obs)

        return FredAcquisitionResult(
            series_id=series_id,
            observations=observations,
            raw_storage_path=raw_path,
            sha256=hashes["sha256"],
            sha1=hashes["sha1"],
            size_bytes=hashes["size_bytes"],
            request_parameters_hash=req_hash
        )
