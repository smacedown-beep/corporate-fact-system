"""
OpenDART Acquisition Client.
Strictly conforms to official FSS OpenDART developer guidelines.
Implements ZIP signature verification, integrity testing, XML extraction,
and immutable raw evidence preservation.
"""
import io
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from config.settings import settings
from src.core.enums import SourceProvider, SourceType
from src.core.hashing import compute_hashes
from src.core.security import hash_request_params, sanitize_params
from src.core.exceptions import (
    ForensicError,
    ProvenanceSystemError,
    SecurityViolationError
)
from src.connectors.base import BaseConnector

# Receipt number format: exactly 14 digits (YYYYMMDD00xxxx)
RECEIPT_REGEX = re.compile(r"^\d{14}$")
ZIP_MAGIC_SIGNATURE = b"PK\x03\x04"


@dataclass
class DartDocumentAcquisition:
    rcept_no: str
    source_provider: str = SourceProvider.DART.value
    source_type: str = SourceType.API.value
    api_endpoint: str = "https://opendart.fss.or.kr/api/document.xml"
    request_parameters_hash: str = ""
    corp_code: Optional[str] = None
    stock_code: Optional[str] = None
    company_name: Optional[str] = None
    report_name: Optional[str] = None
    report_period: Optional[str] = None
    filing_date: Optional[str] = None
    acquisition_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    availability_date: Optional[datetime] = None
    file_path: str = ""
    file_size: int = 0
    sha256: str = ""
    sha1: str = ""
    zip_sha256: str = ""
    zip_sha1: str = ""
    zip_path: str = ""
    http_status: int = 200
    xml_parse_status: str = "PASS"
    identity_validation_status: str = "PENDING"
    raw_xml_content: str = ""

    def to_provenance_dict(self) -> Dict[str, Any]:
        """Returns the dictionary for DB recording. Never includes API key."""
        return {
            "source_provider": self.source_provider,
            "source_type": self.source_type,
            "api_endpoint": self.api_endpoint,
            "request_parameters_hash": self.request_parameters_hash,
            "corp_code": self.corp_code,
            "stock_code": self.stock_code,
            "company_name": self.company_name,
            "rcept_no": self.rcept_no,
            "report_name": self.report_name,
            "report_period": self.report_period,
            "filing_date": self.filing_date,
            "acquisition_timestamp": self.acquisition_timestamp.isoformat(),
            "availability_date": self.availability_date.isoformat() if self.availability_date else None,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "sha256": self.sha256,
            "sha1": self.sha1,
            "http_status": self.http_status,
            "xml_parse_status": self.xml_parse_status,
            "identity_validation_status": self.identity_validation_status
        }


class OpenDartClient(BaseConnector):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(SourceProvider.DART)
        self.api_key = api_key or settings.dart_api_key

    def acquire_document_xml(
        self,
        rcept_no: str,
        filing_meta: Optional[Dict[str, Any]] = None,
        mock_zip_bytes: Optional[bytes] = None
    ) -> DartDocumentAcquisition:
        """
        Forensic acquisition procedure for DART document.xml:
        1. Validate receipt number format (14 digits)
        2. Acquire ZIP payload (via HTTP or mock)
        3. Verify ZIP magic signature (PK\x03\x04)
        4. Test ZIP archive integrity (testzip)
        5. Extract primary XML file
        6. Parse and validate XML syntax
        7. Compute dual SHA256 & SHA1 on both ZIP and XML
        8. Immutably preserve raw evidence to disk
        9. Assemble complete provenance metadata
        """
        if not RECEIPT_REGEX.match(rcept_no):
            raise ForensicError(
                f"Invalid DART receipt number format: '{rcept_no}'. "
                f"Receipt must be exactly 14 digits (YYYYMMDD00xxxx)."
            )

        endpoint = "https://opendart.fss.or.kr/api/document.xml"
        params = {"rcept_no": rcept_no}
        req_hash = hash_request_params(params)

        self._enforce_rate_limit()

        # Step 2: Acquire ZIP bytes
        if mock_zip_bytes is not None:
            zip_bytes = mock_zip_bytes
            http_status = 200
        else:
            if not self.api_key:
                raise ProvenanceSystemError(
                    "DART_API_KEY environment variable is not configured. "
                    "Cannot acquire live document from OpenDART without official credentials."
                )
            # In a live request, execute with standard urllib or requests
            import urllib.request
            req_params = dict(params)
            req_params["crtfc_key"] = self.api_key
            url = f"{endpoint}?rcept_no={rcept_no}&crtfc_key={self.api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorporateInvestProvenance/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                http_status = resp.status
                zip_bytes = resp.read()

        # Step 3: Check DART error response in case an error message was returned
        if zip_bytes.startswith(b"{") or zip_bytes.startswith(b"<result>"):
            err_msg = zip_bytes.decode("utf-8", errors="replace")
            raise ForensicError(f"OpenDART returned error response instead of ZIP file: {err_msg[:200]}")

        # Step 3: Verify ZIP signature
        if not zip_bytes.startswith(ZIP_MAGIC_SIGNATURE):
            raise ForensicError(
                f"Forensic Acquisition FAIL: Byte stream does not contain valid ZIP signature. "
                f"Expected '{ZIP_MAGIC_SIGNATURE.hex()}', found '{zip_bytes[:4].hex()}'."
            )

        # Step 4: Verify ZIP integrity
        try:
            zip_buffer = io.BytesIO(zip_bytes)
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                bad_file = zf.testzip()
                if bad_file:
                    raise ForensicError(f"Corrupt ZIP file detected in DART acquisition: {bad_file}")

                # Step 5: Extract primary XML file
                xml_names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
                if not xml_names:
                    raise ForensicError(f"No XML document found inside acquired DART ZIP for receipt {rcept_no}.")
                
                # Use document.xml if present, else first xml
                target_xml_name = "document.xml" if "document.xml" in xml_names else xml_names[0]
                raw_xml_bytes = zf.read(target_xml_name)
        except zipfile.BadZipFile as e:
            raise ForensicError(f"Failed to open DART ZIP archive for receipt {rcept_no}: {str(e)}")

        # Step 6: Validate XML syntax
        try:
            # Decode using EUC-KR, CP949, or UTF-8 depending on XML encoding declaration
            xml_text = None
            for enc in ["utf-8", "euc-kr", "cp949"]:
                try:
                    xml_text = raw_xml_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            if xml_text is None:
                xml_text = raw_xml_bytes.decode("utf-8", errors="replace")

            ET.fromstring(raw_xml_bytes)
            xml_parse_status = "PASS"
        except ET.ParseError as e:
            xml_parse_status = f"PARSE_ERROR: {str(e)}"

        # Step 7 & 8: Compute dual hashes and preserve files immutably
        zip_path, zip_hashes = self.preserve_response(
            zip_bytes, extension="zip", subfolder=rcept_no, prefix=f"dart_{rcept_no}"
        )
        xml_path, xml_hashes = self.preserve_response(
            raw_xml_bytes, extension="xml", subfolder=rcept_no, prefix=f"doc_{rcept_no}"
        )

        # Availability date parsing from filing_date
        filing_meta = filing_meta or {}
        filing_date_str = filing_meta.get("filing_date") or rcept_no[:8]
        try:
            avail_date = datetime.strptime(filing_date_str[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
        except Exception:
            avail_date = datetime.now(timezone.utc)

        return DartDocumentAcquisition(
            rcept_no=rcept_no,
            api_endpoint=endpoint,
            request_parameters_hash=req_hash,
            corp_code=filing_meta.get("corp_code"),
            stock_code=filing_meta.get("stock_code"),
            company_name=filing_meta.get("company_name"),
            report_name=filing_meta.get("report_name"),
            report_period=filing_meta.get("report_period"),
            filing_date=filing_date_str,
            acquisition_timestamp=datetime.now(timezone.utc),
            availability_date=avail_date,
            file_path=xml_path,
            file_size=xml_hashes["size_bytes"],
            sha256=xml_hashes["sha256"],
            sha1=xml_hashes["sha1"],
            zip_path=zip_path,
            zip_sha256=zip_hashes["sha256"],
            zip_sha1=zip_hashes["sha1"],
            http_status=http_status,
            xml_parse_status=xml_parse_status,
            identity_validation_status="PENDING",
            raw_xml_content=xml_text
        )
