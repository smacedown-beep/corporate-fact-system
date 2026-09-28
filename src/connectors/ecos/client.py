"""
ECOS (Bank of Korea Economic Statistics System) Connector.
Conforms strictly to Bank of Korea OpenAPI developer specification:
URL: https://ecos.bok.or.kr/api/{serviceName}/{apiKey}/{type}/{language}/{startCount}/{endCount}/{statCode}/{cycle}/{startDate}/{endDate}/{itemCode1}
Enforces rate limiting, parameter hashing without API key,
immutable raw response preservation, and observation mapping.
"""
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from config.settings import settings
from src.core.enums import SourceProvider, SourceType
from src.core.security import hash_request_params
from src.core.exceptions import (
    ForensicError,
    ProvenanceSystemError
)
from src.connectors.base import BaseConnector

CYCLE_REGEX = re.compile(r"^(DD|MM|QQ|YY)$")


@dataclass
class EcosObservation:
    stat_code: str
    stat_name: str
    cycle: str
    time: str
    item_code: str
    item_name: str
    data_value: float
    unit: str
    availability_date: datetime
    raw_storage_path: str
    raw_sha256: str


@dataclass
class EcosAcquisitionResult:
    stat_code: str
    observations: List[EcosObservation]
    raw_storage_path: str
    sha256: str
    sha1: str
    size_bytes: int
    request_parameters_hash: str


class EcosClient(BaseConnector):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(SourceProvider.ECOS)
        self.api_key = api_key or settings.ecos_api_key

    def search_statistics(
        self,
        stat_code: str,
        cycle: str,
        start_date: str,
        end_date: str,
        item_code1: str,
        start_count: int = 1,
        end_count: int = 1000,
        item_code2: Optional[str] = None,
        mock_json_payload: Optional[str] = None
    ) -> EcosAcquisitionResult:
        """
        Executes StatisticSearch API call conforming to Bank of Korea URL format.
        """
        if not CYCLE_REGEX.match(cycle.upper()):
            raise ForensicError(f"Invalid ECOS cycle '{cycle}'. Allowed cycles: DD, MM, QQ, YY.")

        # Parameters without API key for reproducible hash
        params = {
            "service": "StatisticSearch",
            "stat_code": stat_code,
            "cycle": cycle.upper(),
            "start_date": start_date,
            "end_date": end_date,
            "item_code1": item_code1,
            "item_code2": item_code2 or "",
            "start_count": start_count,
            "end_count": end_count
        }
        req_hash = hash_request_params(params)
        self._enforce_rate_limit()

        if mock_json_payload is not None:
            raw_bytes = mock_json_payload.encode("utf-8")
        else:
            if not self.api_key:
                raise ProvenanceSystemError(
                    "ECOS_API_KEY environment variable is not configured. "
                    "Cannot acquire live economic statistics from Bank of Korea."
                )
            import urllib.request
            # Official BOK REST Path URL format:
            # /api/StatisticSearch/{apiKey}/json/kr/{start}/{end}/{statCode}/{cycle}/{startDe}/{endDe}/{itm1}/{itm2}
            path_parts = [
                "https://ecos.bok.or.kr/api/StatisticSearch",
                self.api_key,
                "json",
                "kr",
                str(start_count),
                str(end_count),
                stat_code,
                cycle.upper(),
                start_date,
                end_date,
                item_code1
            ]
            if item_code2:
                path_parts.append(item_code2)

            url = "/".join(path_parts)
            req = urllib.request.Request(url, headers={"User-Agent": "CorporateInvestProvenance/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_bytes = resp.read()

        # Parse JSON
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ForensicError(f"Failed to parse ECOS JSON response: {str(e)}")

        # Check for BOK error response
        if "RESULT" in data:
            code = data["RESULT"].get("CODE", "")
            msg = data["RESULT"].get("MESSAGE", "")
            if code != "INFO-000":
                raise ForensicError(f"ECOS API Error returned from Bank of Korea: [{code}] {msg}")

        # Preserve raw JSON payload immutably
        raw_path, hashes = self.preserve_response(
            raw_bytes, extension="json", subfolder=stat_code, prefix=f"ecos_{stat_code}"
        )

        observations = []
        rows = []
        if "StatisticSearch" in data and "row" in data["StatisticSearch"]:
            rows = data["StatisticSearch"]["row"]

        for row in rows:
            stat_cd = row.get("STAT_CODE", stat_code)
            stat_nm = row.get("STAT_NAME", "")
            itm_cd = row.get("ITEM_CODE1", item_code1)
            itm_nm = row.get("ITEM_NAME1", "")
            t_period = row.get("TIME", "")
            val_str = row.get("DATA_VALUE", "0")
            unit_nm = row.get("UNIT_NAME", "")

            try:
                num_val = float(val_str.replace(",", ""))
            except ValueError:
                num_val = 0.0

            # ECOS availability: BOK publishes market data daily after 16:30 KST
            avail_date = datetime.now(timezone.utc)

            obs = EcosObservation(
                stat_code=stat_cd,
                stat_name=stat_nm,
                cycle=cycle.upper(),
                time=t_period,
                item_code=itm_cd,
                item_name=itm_nm,
                data_value=num_val,
                unit=unit_nm,
                availability_date=avail_date,
                raw_storage_path=raw_path,
                raw_sha256=hashes["sha256"]
            )
            observations.append(obs)

        return EcosAcquisitionResult(
            stat_code=stat_code,
            observations=observations,
            raw_storage_path=raw_path,
            sha256=hashes["sha256"],
            sha1=hashes["sha1"],
            size_bytes=hashes["size_bytes"],
            request_parameters_hash=req_hash
        )
