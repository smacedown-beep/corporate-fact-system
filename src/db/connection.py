"""
Database Connection Manager and Gate Enforcement Layer.
Provides database access with strict DbWriteGate and immutability controls.
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from config.settings import settings
from src.core.gates import DbWriteGate
from src.core.exceptions import (
    GateBlockedError,
    ForensicError,
    SecurityViolationError
)

# Tables that are strictly append-only
IMMUTABLE_TABLES = {"raw_observation", "source_acquisition_log", "audit_log"}


class DatabaseEngine:
    """
    Unified database engine providing connection management,
    execution gate verification, and immutability checks.
    """
    def __init__(
        self,
        db_path: Optional[str] = None,
        write_gate: Optional[DbWriteGate] = None
    ):
        self.write_gate = write_gate or DbWriteGate(settings.execution_mode)
        self.is_sqlite = True
        self.db_path = db_path or ":memory:"
        self._conn = None
        self._init_connection()

    def _init_connection(self):
        # Enforce legacy DB name check
        if settings.db_name.lower() in {"corporate_investment", "corporate_invest"}:
            raise SecurityViolationError(f"Attempted connection to legacy database: {settings.db_name}")

        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_sqlite_schema()

    def _create_sqlite_schema(self):
        """Creates the identical 10-table schema with triggers for SQLite environments."""
        cur = self._conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS company_master (
            company_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            company_name_en TEXT,
            corp_code TEXT NOT NULL UNIQUE,
            stock_code TEXT,
            market TEXT,
            country TEXT DEFAULT 'KR',
            industry_code TEXT,
            industry_name TEXT,
            status TEXT DEFAULT 'ACTIVE',
            effective_from TEXT NOT NULL,
            effective_to TEXT
        );

        CREATE TABLE IF NOT EXISTS source_registry (
            source_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            authority_level INTEGER NOT NULL,
            official_url TEXT NOT NULL,
            api_endpoint TEXT,
            authentication_type TEXT NOT NULL,
            api_key_env TEXT,
            dataset_code TEXT,
            table_code TEXT,
            series_code TEXT,
            unit TEXT,
            frequency TEXT,
            availability_rule TEXT,
            active INTEGER DEFAULT 1,
            last_verified_at TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_acquisition_log (
            acquisition_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL REFERENCES source_registry(source_id),
            endpoint TEXT NOT NULL,
            http_method TEXT NOT NULL,
            request_parameters_hash TEXT NOT NULL,
            http_status INTEGER NOT NULL,
            response_sha256 TEXT NOT NULL,
            response_sha1 TEXT NOT NULL,
            raw_storage_path TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            acquired_at TEXT NOT NULL,
            parser_version TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS raw_observation (
            raw_id TEXT PRIMARY KEY,
            acquisition_id TEXT NOT NULL REFERENCES source_acquisition_log(acquisition_id),
            company_id TEXT REFERENCES company_master(company_id),
            entity_identity_hash TEXT,
            source_record_identifier TEXT,
            observation_period TEXT NOT NULL,
            source_update_date TEXT NOT NULL,
            availability_date TEXT NOT NULL,
            raw_metric_name TEXT NOT NULL,
            raw_value_text TEXT NOT NULL,
            raw_value_numeric REAL,
            unit TEXT NOT NULL,
            source_location_metadata TEXT,
            validation_status TEXT DEFAULT 'RAW',
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS derived_observation (
            derived_id TEXT PRIMARY KEY,
            company_id TEXT REFERENCES company_master(company_id),
            metric_name TEXT NOT NULL,
            derived_value REAL NOT NULL,
            unit TEXT NOT NULL,
            formula TEXT NOT NULL,
            calculation_version TEXT NOT NULL,
            calculated_at TEXT NOT NULL,
            availability_date TEXT NOT NULL,
            validation_status TEXT DEFAULT 'DERIVED'
        );

        CREATE TABLE IF NOT EXISTS composite_indicator (
            composite_id TEXT PRIMARY KEY,
            indicator_name TEXT NOT NULL,
            composite_value REAL NOT NULL,
            components_spec TEXT NOT NULL,
            formula TEXT NOT NULL,
            availability_date TEXT NOT NULL,
            validation_status TEXT DEFAULT 'COMPOSITE',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS data_lineage (
            lineage_id TEXT PRIMARY KEY,
            parent_entity_type TEXT NOT NULL,
            parent_id TEXT NOT NULL,
            child_entity_type TEXT NOT NULL,
            child_id TEXT NOT NULL,
            transformation_rule TEXT,
            software_version TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS forensic_evidence (
            evidence_id TEXT PRIMARY KEY,
            target_type TEXT NOT NULL,
            target_identifier TEXT,
            detected_issue TEXT NOT NULL,
            expected_identity TEXT NOT NULL,
            actual_identity TEXT NOT NULL,
            raw_evidence_hash TEXT,
            detected_at TEXT NOT NULL,
            status TEXT DEFAULT 'BLOCKED'
        );

        CREATE TABLE IF NOT EXISTS canonical_reconciliation (
            reconciliation_id TEXT PRIMARY KEY,
            company_id TEXT REFERENCES company_master(company_id),
            metric_name TEXT NOT NULL,
            period TEXT NOT NULL,
            canonical_value REAL,
            official_value REAL,
            difference REAL,
            receipt_match INTEGER,
            identity_match INTEGER,
            provenance_status TEXT,
            reconciled_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY,
            actor TEXT NOT NULL,
            operation TEXT NOT NULL,
            source TEXT,
            record_id TEXT,
            before_hash TEXT,
            after_hash TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            metadata TEXT,
            timestamp TEXT NOT NULL
        );

        -- Immutability triggers for SQLite
        CREATE TRIGGER IF NOT EXISTS trg_immutable_raw_update
        BEFORE UPDATE ON raw_observation
        BEGIN
            SELECT RAISE(ABORT, 'FORENSIC_ERROR: raw_observation is strictly append-only. UPDATE prohibited.');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_immutable_raw_delete
        BEFORE DELETE ON raw_observation
        BEGIN
            SELECT RAISE(ABORT, 'FORENSIC_ERROR: raw_observation is strictly append-only. DELETE prohibited.');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_immutable_acq_update
        BEFORE UPDATE ON source_acquisition_log
        BEGIN
            SELECT RAISE(ABORT, 'FORENSIC_ERROR: source_acquisition_log is strictly append-only. UPDATE prohibited.');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_immutable_acq_delete
        BEFORE DELETE ON source_acquisition_log
        BEGIN
            SELECT RAISE(ABORT, 'FORENSIC_ERROR: source_acquisition_log is strictly append-only. DELETE prohibited.');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_immutable_audit_update
        BEFORE UPDATE ON audit_log
        BEGIN
            SELECT RAISE(ABORT, 'FORENSIC_ERROR: audit_log is strictly append-only. UPDATE prohibited.');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_immutable_audit_delete
        BEFORE DELETE ON audit_log
        BEGIN
            SELECT RAISE(ABORT, 'FORENSIC_ERROR: audit_log is strictly append-only. DELETE prohibited.');
        END;
        """)
        self._conn.commit()

    def execute_write(self, sql: str, params: tuple = ()) -> int:
        """
        Executes a mutating query after passing through the DbWriteGate and Immutability checks.
        """
        sql_upper = sql.strip().upper()
        op_name = sql_upper.split()[0] if sql_upper else "UNKNOWN"

        # Check write gate
        self.write_gate.assert_can_write(f"{op_name} query: {sql[:40]}...")

        # Application-level check for immutable tables
        for table in IMMUTABLE_TABLES:
            if table in sql.lower() and (sql_upper.startswith("UPDATE") or sql_upper.startswith("DELETE")):
                raise ForensicError(
                    f"CRITICAL: Modification attempt on immutable table '{table}' is strictly prohibited."
                )

        cur = self._conn.cursor()
        cur.execute(sql, params)
        self._conn.commit()
        return cur.rowcount

    def execute_query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Executes a read-only query (always allowed, does not require write gate)."""
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def close(self):
        if self._conn:
            self._conn.close()
