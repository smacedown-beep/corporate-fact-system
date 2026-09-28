"""
Data Repository Layer for the 10 Core Tables.
All mutating actions verify the DbWriteGate and generate structured audit entries.
"""
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from src.db.connection import DatabaseEngine
from src.db.models import (
    CompanyMaster,
    SourceRegistry,
    SourceAcquisitionLog,
    RawObservation,
    DerivedObservation,
    CompositeIndicator,
    DataLineage,
    ForensicEvidence,
    CanonicalReconciliation,
    AuditLog
)
from src.core.enums import ValidationStatus


class ProvenanceRepository:
    def __init__(self, engine: DatabaseEngine):
        self.engine = engine

    # --- 1. Company Master ---
    def insert_company(self, company: CompanyMaster) -> str:
        sql = """
        INSERT INTO company_master (
            company_id, company_name, company_name_en, corp_code,
            stock_code, market, country, industry_code, industry_name,
            status, effective_from, effective_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            company.company_id, company.company_name, company.company_name_en,
            company.corp_code, company.stock_code, company.market, company.country,
            company.industry_code, company.industry_name, company.status,
            company.effective_from.isoformat(),
            company.effective_to.isoformat() if company.effective_to else None
        )
        self.engine.execute_write(sql, params)
        return company.company_id

    def get_company_by_corp_code(self, corp_code: str) -> Optional[Dict[str, Any]]:
        rows = self.engine.execute_query(
            "SELECT * FROM company_master WHERE corp_code = ?", (corp_code,)
        )
        return dict(rows[0]) if rows else None

    # --- 2. Source Registry ---
    def insert_source(self, source: SourceRegistry) -> str:
        sql = """
        INSERT INTO source_registry (
            source_id, provider, source_name, source_type, authority_level,
            official_url, api_endpoint, authentication_type, api_key_env,
            dataset_code, table_code, series_code, unit, frequency,
            availability_rule, active, last_verified_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now(timezone.utc).isoformat()
        params = (
            source.source_id, source.provider.value, source.source_name,
            source.source_type.value, int(source.authority_level.value),
            source.official_url, source.api_endpoint, source.authentication_type,
            source.api_key_env, source.dataset_code, source.table_code,
            source.series_code, source.unit, source.frequency,
            source.availability_rule, 1 if source.active else 0,
            source.last_verified_at.isoformat() if source.last_verified_at else None,
            now
        )
        self.engine.execute_write(sql, params)
        return source.source_id

    # --- 3. Source Acquisition Log ---
    def insert_acquisition_log(self, acq: SourceAcquisitionLog) -> str:
        sql = """
        INSERT INTO source_acquisition_log (
            acquisition_id, source_id, endpoint, http_method,
            request_parameters_hash, http_status, response_sha256,
            response_sha1, raw_storage_path, file_size_bytes,
            acquired_at, parser_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            acq.acquisition_id, acq.source_id, acq.endpoint, acq.http_method,
            acq.request_parameters_hash, acq.http_status, acq.response_sha256,
            acq.response_sha1, acq.raw_storage_path, acq.file_size_bytes,
            acq.acquired_at.isoformat(), acq.parser_version
        )
        self.engine.execute_write(sql, params)
        return acq.acquisition_id

    # --- 4. Raw Observation (Append-Only) ---
    def insert_raw_observation(self, raw: RawObservation) -> str:
        sql = """
        INSERT INTO raw_observation (
            raw_id, acquisition_id, company_id, entity_identity_hash,
            source_record_identifier, observation_period, source_update_date,
            availability_date, raw_metric_name, raw_value_text,
            raw_value_numeric, unit, source_location_metadata,
            validation_status, version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            raw.raw_id, raw.acquisition_id, raw.company_id, raw.entity_identity_hash,
            raw.source_record_identifier, raw.observation_period,
            raw.source_update_date.isoformat(), raw.availability_date.isoformat(),
            raw.raw_metric_name, raw.raw_value_text,
            float(raw.raw_value_numeric) if raw.raw_value_numeric is not None else None,
            raw.unit,
            json.dumps(raw.source_location_metadata) if raw.source_location_metadata else None,
            raw.validation_status.value, raw.version, raw.created_at.isoformat()
        )
        self.engine.execute_write(sql, params)
        return raw.raw_id

    # --- 5. Derived Observation ---
    def insert_derived_observation(self, derived: DerivedObservation) -> str:
        sql = """
        INSERT INTO derived_observation (
            derived_id, company_id, metric_name, derived_value, unit,
            formula, calculation_version, calculated_at,
            availability_date, validation_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            derived.derived_id, derived.company_id, derived.metric_name,
            float(derived.derived_value), derived.unit, derived.formula,
            derived.calculation_version, derived.calculated_at.isoformat(),
            derived.availability_date.isoformat(), derived.validation_status.value
        )
        self.engine.execute_write(sql, params)
        return derived.derived_id

    # --- 6. Data Lineage ---
    def insert_lineage(self, lineage: DataLineage) -> str:
        sql = """
        INSERT INTO data_lineage (
            lineage_id, parent_entity_type, parent_id, child_entity_type,
            child_id, transformation_rule, software_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            lineage.lineage_id, lineage.parent_entity_type, lineage.parent_id,
            lineage.child_entity_type, lineage.child_id, lineage.transformation_rule,
            lineage.software_version, lineage.created_at.isoformat()
        )
        self.engine.execute_write(sql, params)
        return lineage.lineage_id

    # --- 7. Forensic Evidence ---
    def insert_forensic_evidence(self, evidence: ForensicEvidence) -> str:
        sql = """
        INSERT INTO forensic_evidence (
            evidence_id, target_type, target_identifier, detected_issue,
            expected_identity, actual_identity, raw_evidence_hash,
            detected_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            evidence.evidence_id, evidence.target_type, evidence.target_identifier,
            evidence.detected_issue, json.dumps(evidence.expected_identity),
            json.dumps(evidence.actual_identity), evidence.raw_evidence_hash,
            evidence.detected_at.isoformat(), evidence.status
        )
        self.engine.execute_write(sql, params)
        return evidence.evidence_id

    # --- 8. Audit Log ---
    def insert_audit_log(self, audit: AuditLog) -> str:
        sql = """
        INSERT INTO audit_log (
            audit_id, actor, operation, source, record_id,
            before_hash, after_hash, status, error_message, metadata, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            audit.audit_id, audit.actor, audit.operation, audit.source,
            audit.record_id, audit.before_hash, audit.after_hash,
            audit.status, audit.error_message,
            json.dumps(audit.metadata) if audit.metadata else None,
            audit.timestamp.isoformat()
        )
        self.engine.execute_write(sql, params)
        return audit.audit_id

    # --- Lineage Query ---
    def get_lineage_parents(self, child_id: str) -> List[Dict[str, Any]]:
        rows = self.engine.execute_query(
            "SELECT * FROM data_lineage WHERE child_id = ?", (child_id,)
        )
        return [dict(r) for r in rows]
