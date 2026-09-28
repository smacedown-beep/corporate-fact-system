"""
Contamination Detection Engine.
Scans the database to identify instances where distinct corporate entities
or conflicting corp_codes are mixed within the same pipeline.
"""
from typing import List, Dict, Any
from src.db.repository import ProvenanceRepository
from src.db.models import ForensicEvidence


class ContaminationDetector:
    def __init__(self, repository: ProvenanceRepository):
        self.repository = repository

    def scan_for_contamination(self, company_id: str, expected_corp_code: str) -> List[Dict[str, Any]]:
        """
        Verifies that all raw observations associated with company_id belong
        strictly to expected_corp_code.
        """
        # Query raw observations linked to company_id
        sql = """
        SELECT r.raw_id, r.source_record_identifier, r.entity_identity_hash, r.observation_period,
               c.corp_code, c.company_name
        FROM raw_observation r
        JOIN company_master c ON r.company_id = c.company_id
        WHERE r.company_id = ?
        """
        rows = self.repository.engine.execute_query(sql, (company_id,))
        contaminations = []

        for row in rows:
            rec = dict(row)
            actual_corp = rec.get("corp_code")
            if actual_corp != expected_corp_code:
                contaminations.append({
                    "raw_id": rec.get("raw_id"),
                    "receipt": rec.get("source_record_identifier"),
                    "expected_corp_code": expected_corp_code,
                    "actual_corp_code": actual_corp,
                    "issue": "CROSS_COMPANY_CONTAMINATION"
                })

        return contaminations
