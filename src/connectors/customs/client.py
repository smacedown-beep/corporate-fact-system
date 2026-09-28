"""
Korea Customs Service (UNI-PASS) Connector.
Strictly distinguishes Weight (KG) vs Vehicle Count (대) units in HSK 8703 trade data.
Enforces unit clarity to prevent false ASP interpretation.
"""
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from config.settings import settings
from src.core.enums import SourceProvider
from src.core.security import hash_request_params
from src.core.exceptions import ForensicError, ProvenanceSystemError
from src.connectors.base import BaseConnector


@dataclass
class CustomsTradeRecord:
    hsk_code: str
    year_month: str
    export_usd: float
    import_usd: float
    export_weight_kg: float
    export_count: Optional[int]
    unit_basis: str  # "KG" or "COUNT" or "BOTH"
    raw_storage_path: str
    raw_sha256: str


@dataclass
class CustomsAcquisitionResult:
    hsk_code: str
    records: List[CustomsTradeRecord]
    raw_storage_path: str
    sha256: str
    sha1: str
    size_bytes: int


class CustomsClient(BaseConnector):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(SourceProvider.CUSTOMS)
        self.api_key = api_key or settings.customs_api_key

    def acquire_hsk_trade(
        self,
        hsk_code: str,
        start_ym: str,
        end_ym: str,
        mock_payload: Optional[str] = None
    ) -> CustomsAcquisitionResult:
        endpoint = "https://unipass.customs.go.kr/openapi/services/trade/hskTrade"
        params = {
            "hskCode": hsk_code,
            "startYearMonth": start_ym,
            "endYearMonth": end_ym
        }
        self._enforce_rate_limit()

        if mock_payload is not None:
            raw_bytes = mock_payload.encode("utf-8")
        else:
            if not self.api_key:
                raise ProvenanceSystemError("CUSTOMS_API_KEY environment variable is not configured.")
            import urllib.request
            req_params = dict(params)
            req_params["crkyCn"] = self.api_key
            query_str = "&".join(f"{k}={v}" for k, v in req_params.items())
            url = f"{endpoint}?{query_str}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorporateInvestProvenance/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_bytes = resp.read()

        raw_path, hashes = self.preserve_response(
            raw_bytes, extension="json", subfolder=hsk_code, prefix=f"customs_{hsk_code}"
        )

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception:
            raise ForensicError("Failed to parse Customs response payload.")

        records = []
        for item in data.get("items", []):
            ym = item.get("year_month", "")
            exp_usd = float(item.get("export_usd", 0.0))
            imp_usd = float(item.get("import_usd", 0.0))
            exp_kg = float(item.get("export_weight_kg", 0.0))
            exp_cnt = item.get("export_count")
            exp_cnt_val = int(exp_cnt) if exp_cnt is not None else None

            # Forensic Unit Check: Determine unit basis
            unit_basis = "BOTH" if exp_cnt_val is not None else "KG"

            rec = CustomsTradeRecord(
                hsk_code=hsk_code,
                year_month=ym,
                export_usd=exp_usd,
                import_usd=imp_usd,
                export_weight_kg=exp_kg,
                export_count=exp_cnt_val,
                unit_basis=unit_basis,
                raw_storage_path=raw_path,
                raw_sha256=hashes["sha256"]
            )
            records.append(rec)

        return CustomsAcquisitionResult(
            hsk_code=hsk_code,
            records=records,
            raw_storage_path=raw_path,
            sha256=hashes["sha256"],
            sha1=hashes["sha1"],
            size_bytes=hashes["size_bytes"]
        )
