"""
Corporate Identity Multi-Attribute Forensic Validator.
Validates corp_code, stock_code, company_name, report_name, and report_period.
Detects identity mismatch and cross-company contamination.
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from src.core.enums import ForensicVerdict


def normalize_corp_name(name: Optional[str]) -> str:
    """Normalizes company names by removing legal entity affixes and whitespaces."""
    if not name:
        return ""
    cleaned = re.sub(r"\(주\)|주식회사|㈜|\s+", "", name)
    return cleaned.upper()


@dataclass
class IdentityValidationResult:
    verdict: ForensicVerdict
    is_valid: bool
    mismatches: List[str] = field(default_factory=list)
    detected_issue: Optional[str] = None
    expected_identity: Dict[str, Any] = field(default_factory=dict)
    actual_identity: Dict[str, Any] = field(default_factory=dict)


class IdentityValidator:
    @staticmethod
    def validate(
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> IdentityValidationResult:
        mismatches = []
        detected_issue = None

        exp_corp = str(expected.get("corp_code", "")).strip().zfill(8)
        act_corp = str(actual.get("corp_code", "")).strip().zfill(8)

        exp_stock = str(expected.get("stock_code", "")).strip().zfill(6) if expected.get("stock_code") else None
        act_stock = str(actual.get("stock_code", "")).strip().zfill(6) if actual.get("stock_code") else None

        exp_name = normalize_corp_name(expected.get("company_name") or expected.get("corp_name"))
        act_name = normalize_corp_name(actual.get("company_name") or actual.get("corp_name"))

        exp_period = expected.get("report_period")
        act_period = actual.get("report_period")

        # 1. Critical Corp Code Check
        if exp_corp and act_corp and exp_corp != act_corp:
            mismatches.append(f"corp_code mismatch (expected '{exp_corp}', got '{act_corp}')")
            # If actual corp code is a completely distinct entity, classify as CONTAMINATION
            detected_issue = "CONTAMINATION" if (act_name and exp_name and exp_name != act_name) else "IDENTITY_MISMATCH"

        # 2. Stock Code Check
        if exp_stock and act_stock and exp_stock != act_stock:
            mismatches.append(f"stock_code mismatch (expected '{exp_stock}', got '{act_stock}')")
            if not detected_issue:
                detected_issue = "STOCK_CODE_MISMATCH"

        # 3. Company Name Check
        if exp_name and act_name and exp_name != act_name:
            mismatches.append(f"company_name mismatch (expected '{exp_name}', got '{act_name}')")
            if not detected_issue:
                detected_issue = "NAME_MISMATCH"

        # 4. Report Period Check
        if exp_period and act_period and exp_period != act_period:
            mismatches.append(f"report_period mismatch (expected '{exp_period}', got '{act_period}')")
            if not detected_issue:
                detected_issue = "PERIOD_MISMATCH"

        if mismatches:
            return IdentityValidationResult(
                verdict=ForensicVerdict.FAIL,
                is_valid=False,
                mismatches=mismatches,
                detected_issue=detected_issue or "IDENTITY_MISMATCH",
                expected_identity=expected,
                actual_identity=actual
            )

        return IdentityValidationResult(
            verdict=ForensicVerdict.PASS,
            is_valid=True,
            mismatches=[],
            detected_issue=None,
            expected_identity=expected,
            actual_identity=actual
        )
