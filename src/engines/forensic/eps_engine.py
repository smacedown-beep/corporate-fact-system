"""
EPS Forensic Engine.
Performs independent recalculation of Basic Earnings Per Share (EPS)
from official DART XML Footnote (Note 30 '주당이익').
Reconciles numerator, weighted average common shares, and rounding differences.
"""
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.core.enums import ForensicVerdict, ValidationStatus
from src.db.models import CanonicalReconciliation
from src.db.repository import ProvenanceRepository


@dataclass
class EpsForensicVerdict:
    rcept_no: str
    company_name: str
    period: str
    official_numerator: Decimal
    official_shares: Decimal
    reported_eps: Decimal
    calculated_eps: Decimal
    eps_difference: Decimal
    rounding_rule: str
    verdict: ForensicVerdict
    is_valid: bool
    reconciliation_status: str
    note_location: str


class EpsForensicEngine:
    def __init__(self, repository: Optional[ProvenanceRepository] = None):
        self.repository = repository
        self.rounding_tolerance = Decimal("1.0")  # Tolerance for fractional won rounding

    def extract_eps_note_from_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parses DART document.xml to locate Note 30 and extract:
        - 지배주주 귀속 순이익 (numerator)
        - 가중평균보통주식수 (shares)
        - 기본주당이익 (reported_eps)
        """
        root = ET.fromstring(xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content)

        extracted = {
            "numerator": None,
            "shares": None,
            "reported_eps": None,
            "note_title": "30. 주당이익"
        }

        # Scan for TABLE or ROW containing EPS items
        for row in root.iter("ROW"):
            row_id = row.attrib.get("id", "")
            cells = row.findall("CELL")
            text_cells = [c.text.strip() for c in cells if c.text]

            for c in cells:
                col = c.attrib.get("col", "")
                val = c.text.strip() if c.text else ""

                if "numerator" in row_id or "지배" in "".join(text_cells):
                    if col in ("amount", "val") and val.replace("-", "").isdigit():
                        extracted["numerator"] = Decimal(val)
                elif "shares" in row_id or "가중평균" in "".join(text_cells):
                    if col in ("shares", "val") and val.replace(",", "").isdigit():
                        extracted["shares"] = Decimal(val.replace(",", ""))
                elif "basic_eps" in row_id or "기본주당" in "".join(text_cells):
                    if col in ("eps", "val") and val.replace(",", "").isdigit():
                        extracted["reported_eps"] = Decimal(val.replace(",", ""))

        return extracted

    def verify_eps(
        self,
        rcept_no: str,
        company_name: str,
        period: str,
        xml_content: str,
        canonical_eps: Optional[Decimal] = None
    ) -> EpsForensicVerdict:
        """
        Extracts note values, executes independent calculation:
        calculated_eps = numerator / weighted_average_shares
        and compares with reported EPS and legacy canonical EPS.
        """
        note_data = self.extract_eps_note_from_xml(xml_content)

        numerator = note_data.get("numerator")
        shares = note_data.get("shares")
        reported_eps = note_data.get("reported_eps")

        if numerator is None or shares is None or reported_eps is None:
            # Fallback or missing note
            raise ValueError(f"Could not extract complete EPS note data from XML for receipt {rcept_no}.")

        # Independent calculation
        calculated_exact = (numerator / shares)
        # Standard financial rounding (round to nearest whole KRW)
        calculated_rounded = calculated_exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        diff = abs(reported_eps - calculated_rounded)

        is_valid = diff <= self.rounding_tolerance
        verdict = ForensicVerdict.PASS if is_valid else ForensicVerdict.FAIL

        # Canonical reconciliation check
        reconciliation_status = "MATCH"
        if canonical_eps is not None:
            if canonical_eps != reported_eps:
                reconciliation_status = "VALUE_MISMATCH"

        return EpsForensicVerdict(
            rcept_no=rcept_no,
            company_name=company_name,
            period=period,
            official_numerator=numerator,
            official_shares=shares,
            reported_eps=reported_eps,
            calculated_eps=calculated_rounded,
            eps_difference=diff,
            rounding_rule="ROUND_HALF_UP_TO_INTEGER_KRW",
            verdict=verdict,
            is_valid=is_valid,
            reconciliation_status=reconciliation_status,
            note_location="Note 30. 주당이익 -> Table: eps_table"
        )
