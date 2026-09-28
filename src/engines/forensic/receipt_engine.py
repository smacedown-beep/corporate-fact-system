"""
Receipt Forensic Engine.
Performs end-to-end receipt forensic verification:
Receipt -> Acquisition -> XML Parse -> Identity Extraction -> Expected vs Actual ->
Hash Check -> Forensic Verdict -> Evidence Quarantine (if FAIL).
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from src.core.enums import ForensicVerdict
from src.core.exceptions import ForensicError
from src.connectors.dart.client import OpenDartClient, DartDocumentAcquisition
from src.engines.forensic.identity_validator import IdentityValidator, IdentityValidationResult
from src.db.models import ForensicEvidence, AuditLog
from src.db.repository import ProvenanceRepository


@dataclass
class ReceiptForensicReport:
    rcept_no: str
    verdict: ForensicVerdict
    is_valid: bool
    detected_issue: Optional[str] = None
    mismatches: List[str] = field(default_factory=list)
    expected_identity: Dict[str, Any] = field(default_factory=dict)
    actual_identity: Dict[str, Any] = field(default_factory=dict)
    acquisition: Optional[DartDocumentAcquisition] = None
    evidence_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def summary(self) -> str:
        status_symbol = "● PASS" if self.verdict == ForensicVerdict.PASS else "■ FAIL"
        lines = [
            f"RECEIPT FORENSIC REPORT: {self.rcept_no}",
            f"Verdict: {status_symbol} ({self.verdict.value})",
            f"Issue Detected: {self.detected_issue or 'NONE'}"
        ]
        if self.mismatches:
            lines.append("Mismatches:")
            for m in self.mismatches:
                lines.append(f"  - {m}")
        return "\n".join(lines)


class ReceiptForensicEngine:
    def __init__(
        self,
        dart_client: Optional[OpenDartClient] = None,
        repository: Optional[ProvenanceRepository] = None
    ):
        self.dart_client = dart_client or OpenDartClient()
        self.repository = repository

    def extract_xml_identity(self, xml_content: str) -> Dict[str, Any]:
        """
        Parses official DART XML header to extract identity attributes.
        """
        actual = {}
        try:
            root = ET.fromstring(xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content)
            # Find in HEADER or root
            header = root.find("HEADER")
            target = header if header is not None else root

            for tag in ["CORP_CODE", "CORP_NAME", "STOCK_CODE", "RCEPT_NO", "REPORT_NAME"]:
                elem = target.find(tag)
                if elem is not None and elem.text:
                    key = tag.lower()
                    actual[key] = elem.text.strip()

            if "corp_name" in actual:
                actual["company_name"] = actual["corp_name"]

            # Infer report period from report_name if present (e.g. '분기보고서 (2023.09)')
            rep_name = actual.get("report_name", "")
            if "(" in rep_name and ")" in rep_name:
                actual["report_period"] = rep_name[rep_name.find("(")+1:rep_name.find(")")]
        except Exception as e:
            actual["parse_error"] = str(e)

        return actual

    def verify_receipt(
        self,
        rcept_no: str,
        expected_identity: Dict[str, Any],
        mock_zip_bytes: Optional[bytes] = None
    ) -> ReceiptForensicReport:
        """
        Executes full forensic pipeline for a given receipt and expected identity.
        """
        # Step 1: Document Acquisition
        acq = self.dart_client.acquire_document_xml(
            rcept_no=rcept_no,
            filing_meta=expected_identity,
            mock_zip_bytes=mock_zip_bytes
        )

        # Step 2: Extract identity from raw XML content
        actual_identity = self.extract_xml_identity(acq.raw_xml_content)

        # Step 3: Multi-attribute cross-validation
        val_res: IdentityValidationResult = IdentityValidator.validate(
            expected=expected_identity,
            actual=actual_identity
        )

        evidence_id = None
        if not val_res.is_valid:
            # Forensic Rule: DO NOT silently delete or pass. Quarantine in forensic_evidence table!
            acq.identity_validation_status = "FAIL"
            if self.repository:
                evidence = ForensicEvidence(
                    target_type="RECEIPT",
                    target_identifier=rcept_no,
                    detected_issue=val_res.detected_issue or "IDENTITY_MISMATCH",
                    expected_identity=expected_identity,
                    actual_identity=actual_identity,
                    raw_evidence_hash=acq.sha256,
                    status="BLOCKED"
                )
                evidence_id = self.repository.insert_forensic_evidence(evidence)

                # Record audit log
                audit = AuditLog(
                    actor="RECEIPT_FORENSIC_ENGINE",
                    operation="VERIFY_RECEIPT",
                    source="DART",
                    record_id=evidence_id,
                    before_hash=acq.sha256,
                    after_hash=acq.sha256,
                    status="FAIL_QUARANTINED",
                    error_message=f"Forensic violation: {val_res.detected_issue}",
                    metadata={"mismatches": val_res.mismatches}
                )
                self.repository.insert_audit_log(audit)

            return ReceiptForensicReport(
                rcept_no=rcept_no,
                verdict=ForensicVerdict.FAIL,
                is_valid=False,
                detected_issue=val_res.detected_issue,
                mismatches=val_res.mismatches,
                expected_identity=expected_identity,
                actual_identity=actual_identity,
                acquisition=acq,
                evidence_id=evidence_id
            )

        # Identity matches perfectly
        acq.identity_validation_status = "PASS"
        if self.repository:
            audit = AuditLog(
                actor="RECEIPT_FORENSIC_ENGINE",
                operation="VERIFY_RECEIPT",
                source="DART",
                before_hash=acq.sha256,
                after_hash=acq.sha256,
                status="PASS",
                metadata={"corp_code": acq.corp_code}
            )
            self.repository.insert_audit_log(audit)

        return ReceiptForensicReport(
            rcept_no=rcept_no,
            verdict=ForensicVerdict.PASS,
            is_valid=True,
            detected_issue=None,
            mismatches=[],
            expected_identity=expected_identity,
            actual_identity=actual_identity,
            acquisition=acq
        )
