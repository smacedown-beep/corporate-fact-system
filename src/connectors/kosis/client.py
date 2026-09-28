"""
KOSIS (Korean Statistical Information Service) Connector.
Implements official OpenAPI data and metadata retrieval,
immutable raw response preservation, and schema/item_code change detection.
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from config.settings import settings
from src.core.enums import SourceProvider, SourceType, AuthorityLevel
from src.core.security import hash_request_params
from src.core.exceptions import (
    ForensicError,
    ProvenanceSystemError,
    UnverifiedSourceError
)
from src.connectors.base import BaseConnector


@dataclass
class KosisObservation:
    org_id: str
    tbl_id: str
    stat_name: str
    item_code: str
    item_name: str
    prd_se: str
    prd_de: str
    value: float
    unit: str
    availability_date: datetime
    raw_storage_path: str
    raw_sha256: str


@dataclass
class KosisAcquisitionResult:
    tbl_id: str
    observations: List[KosisObservation]
    raw_storage_path: str
    sha256: str
    sha1: str
    size_bytes: int
    request_parameters_hash: str
    schema_version: str = "1.0"
    item_codes_found: List[str] = field(default_factory=list)


class KosisClient(BaseConnector):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(SourceProvider.KOSIS)
        self.api_key = api_key or settings.kosis_api_key

    def acquire_statistics_data(
        self,
        org_id: str,
        tbl_id: str,
        prd_se: str,
        start_prd_de: str,
        end_prd_de: str,
        item_id: Optional[str] = None,
        registered_item_codes: Optional[List[str]] = None,
        mock_json_payload: Optional[str] = None
    ) -> KosisAcquisitionResult:
        """
        Acquires statistical observation data from KOSIS.
        Validates schema and detects if any registered item codes changed.
        """
        endpoint = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
        params = {
            "method": "getList",
            "orgId": org_id,
            "tblId": tbl_id,
            "prdSe": prd_se,
            "startPrdDe": start_prd_de,
            "endPrdDe": end_prd_de,
            "format": "json"
        }
        if item_id:
            params["itmId"] = item_id

        req_hash = hash_request_params(params)
        self._enforce_rate_limit()

        if mock_json_payload is not None:
            raw_bytes = mock_json_payload.encode("utf-8")
        else:
            if not self.api_key:
                raise ProvenanceSystemError(
                    "KOSIS_API_KEY environment variable is not configured. "
                    "Cannot acquire live statistics without official credentials."
                )
            import urllib.request
            req_params = dict(params)
            req_params["apiKey"] = self.api_key
            query_str = "&".join(f"{k}={v}" for k, v in req_params.items())
            url = f"{endpoint}?{query_str}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorporateInvestProvenance/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_bytes = resp.read()

        # Check for error payload
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ForensicError(f"Failed to parse KOSIS JSON response: {str(e)}")

        if isinstance(data, dict) and "err" in data:
            raise ForensicError(f"KOSIS API Error returned: {data.get('err')} - {data.get('errMsg')}")

        # Preserve raw JSON payload immutably
        raw_path, hashes = self.preserve_response(
            raw_bytes, extension="json", subfolder=tbl_id, prefix=f"kosis_{tbl_id}"
        )

        observations = []
        found_items = set()

        if isinstance(data, list):
            for row in data:
                # KOSIS standard JSON fields:
                # TBL_ID, TBL_NM, ITM_ID, ITM_NM, PRD_DE, DT, UNIT_NM
                itm_id = row.get("ITM_ID") or row.get("itm_id") or "UNKNOWN"
                itm_nm = row.get("ITM_NM") or row.get("itm_nm") or ""
                stat_nm = row.get("TBL_NM") or row.get("tbl_nm") or ""
                prd_de = row.get("PRD_DE") or row.get("prd_de") or ""
                val_str = row.get("DT") or row.get("dt") or "0"
                unit = row.get("UNIT_NM") or row.get("unit_nm") or ""

                try:
                    num_val = float(val_str)
                except ValueError:
                    num_val = 0.0

                found_items.add(itm_id)

                # Availability date estimation: usually published by the 10th of following month
                # Record explicit availability date
                avail_date = datetime.now(timezone.utc)

                obs = KosisObservation(
                    org_id=org_id,
                    tbl_id=tbl_id,
                    stat_name=stat_nm,
                    item_code=itm_id,
                    item_name=itm_nm,
                    prd_se=prd_se,
                    prd_de=prd_de,
                    value=num_val,
                    unit=unit,
                    availability_date=avail_date,
                    raw_storage_path=raw_path,
                    raw_sha256=hashes["sha256"]
                )
                observations.append(obs)

        # Schema & Item Code Drift Detection
        if registered_item_codes:
            missing_items = set(registered_item_codes) - found_items
            if missing_items:
                # Registered item code disappeared or changed in official KOSIS table
                raise ForensicError(
                    f"KOSIS Schema Drift Alert: Expected item codes {missing_items} not found in {tbl_id}. "
                    f"Found items: {list(found_items)}. Statistical table definition may have changed."
                )

        return KosisAcquisitionResult(
            tbl_id=tbl_id,
            observations=observations,
            raw_storage_path=raw_path,
            sha256=hashes["sha256"],
            sha1=hashes["sha1"],
            size_bytes=hashes["size_bytes"],
            request_parameters_hash=req_hash,
            item_codes_found=sorted(list(found_items))
        )
