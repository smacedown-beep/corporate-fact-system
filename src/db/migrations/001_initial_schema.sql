-- =============================================================================
-- Corporate Investment FACT & Provenance System - PostgreSQL 16+ DDL
-- Target Database: corporate_investment_next
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Company Master Table
CREATE TABLE IF NOT EXISTS company_master (
    company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(128) NOT NULL,
    company_name_en VARCHAR(128),
    corp_code CHAR(8) NOT NULL,
    stock_code CHAR(6),
    market VARCHAR(32),
    country CHAR(2) DEFAULT 'KR',
    industry_code VARCHAR(32),
    industry_name VARCHAR(128),
    status VARCHAR(32) DEFAULT 'ACTIVE',
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    effective_to TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_company_corp_code ON company_master(corp_code);
CREATE INDEX IF NOT EXISTS idx_company_stock_code ON company_master(stock_code);

-- 2. Source Registry Table
CREATE TABLE IF NOT EXISTS source_registry (
    source_id VARCHAR(64) PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    source_name VARCHAR(128) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    authority_level SMALLINT NOT NULL,
    official_url TEXT NOT NULL,
    api_endpoint TEXT,
    authentication_type VARCHAR(32) NOT NULL,
    api_key_env VARCHAR(64),
    dataset_code VARCHAR(64),
    table_code VARCHAR(64),
    series_code VARCHAR(64),
    unit VARCHAR(32),
    frequency VARCHAR(16),
    availability_rule TEXT,
    active BOOLEAN DEFAULT TRUE,
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_source_provider ON source_registry(provider);

-- 3. Source Acquisition Log (Immutable Evidence Record)
CREATE TABLE IF NOT EXISTS source_acquisition_log (
    acquisition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(64) NOT NULL REFERENCES source_registry(source_id),
    endpoint TEXT NOT NULL,
    http_method VARCHAR(8) NOT NULL,
    request_parameters_hash CHAR(64) NOT NULL,
    http_status INTEGER NOT NULL,
    response_sha256 CHAR(64) NOT NULL,
    response_sha1 CHAR(40) NOT NULL,
    raw_storage_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    parser_version VARCHAR(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_acquisition_sha256 ON source_acquisition_log(response_sha256);
CREATE INDEX IF NOT EXISTS idx_acquisition_source_id ON source_acquisition_log(source_id);

-- 4. Raw Observation Table (Strictly Append-Only)
CREATE TABLE IF NOT EXISTS raw_observation (
    raw_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    acquisition_id UUID NOT NULL REFERENCES source_acquisition_log(acquisition_id),
    company_id UUID REFERENCES company_master(company_id),
    entity_identity_hash CHAR(64),
    source_record_identifier VARCHAR(128),
    observation_period VARCHAR(32) NOT NULL,
    source_update_date TIMESTAMPTZ NOT NULL,
    availability_date TIMESTAMPTZ NOT NULL,
    raw_metric_name VARCHAR(128) NOT NULL,
    raw_value_text TEXT NOT NULL,
    raw_value_numeric NUMERIC(24, 6),
    unit VARCHAR(32) NOT NULL,
    source_location_metadata JSONB,
    validation_status VARCHAR(32) DEFAULT 'RAW',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_raw_company_period ON raw_observation(company_id, observation_period);
CREATE INDEX IF NOT EXISTS idx_raw_availability_date ON raw_observation(availability_date);
CREATE INDEX IF NOT EXISTS idx_raw_metric_name ON raw_observation(raw_metric_name);
CREATE INDEX IF NOT EXISTS idx_raw_source_record ON raw_observation(source_record_identifier);

-- 5. Derived Observation Table
CREATE TABLE IF NOT EXISTS derived_observation (
    derived_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_master(company_id),
    metric_name VARCHAR(128) NOT NULL,
    derived_value NUMERIC(24, 6) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    formula TEXT NOT NULL,
    calculation_version VARCHAR(32) NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    availability_date TIMESTAMPTZ NOT NULL,
    validation_status VARCHAR(32) DEFAULT 'DERIVED'
);
CREATE INDEX IF NOT EXISTS idx_derived_company_metric ON derived_observation(company_id, metric_name);
CREATE INDEX IF NOT EXISTS idx_derived_availability ON derived_observation(availability_date);

-- 6. Composite Indicator Table
CREATE TABLE IF NOT EXISTS composite_indicator (
    composite_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_name VARCHAR(128) NOT NULL,
    composite_value NUMERIC(24, 6) NOT NULL,
    components_spec JSONB NOT NULL,
    formula TEXT NOT NULL,
    availability_date TIMESTAMPTZ NOT NULL,
    validation_status VARCHAR(32) DEFAULT 'COMPOSITE',
    created_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_composite_name ON composite_indicator(indicator_name);

-- 7. Data Lineage Table (Complete Provenance Graph)
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_entity_type VARCHAR(32) NOT NULL,
    parent_id UUID NOT NULL,
    child_entity_type VARCHAR(32) NOT NULL,
    child_id UUID NOT NULL,
    transformation_rule TEXT,
    software_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_lineage_parent ON data_lineage(parent_id);
CREATE INDEX IF NOT EXISTS idx_lineage_child ON data_lineage(child_id);

-- 8. Forensic Evidence Table (Tampering, Contamination & Mismatch Quarantine)
CREATE TABLE IF NOT EXISTS forensic_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_type VARCHAR(32) NOT NULL,
    target_identifier VARCHAR(128),
    detected_issue VARCHAR(64) NOT NULL,
    expected_identity JSONB NOT NULL,
    actual_identity JSONB NOT NULL,
    raw_evidence_hash CHAR(64),
    detected_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP(),
    status VARCHAR(32) DEFAULT 'BLOCKED'
);
CREATE INDEX IF NOT EXISTS idx_forensic_target ON forensic_evidence(target_identifier);
CREATE INDEX IF NOT EXISTS idx_forensic_issue ON forensic_evidence(detected_issue);

-- 9. Canonical Reconciliation Table
CREATE TABLE IF NOT EXISTS canonical_reconciliation (
    reconciliation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_master(company_id),
    metric_name VARCHAR(64) NOT NULL,
    period VARCHAR(32) NOT NULL,
    canonical_value NUMERIC(24, 6),
    official_value NUMERIC(24, 6),
    difference NUMERIC(24, 6),
    receipt_match BOOLEAN,
    identity_match BOOLEAN,
    provenance_status VARCHAR(32),
    reconciled_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_reconciliation_company ON canonical_reconciliation(company_id, metric_name, period);

-- 10. Audit Log Table (Immutable Execution Trail)
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor VARCHAR(64) NOT NULL,
    operation VARCHAR(64) NOT NULL,
    source VARCHAR(64),
    record_id UUID,
    before_hash CHAR(64),
    after_hash CHAR(64),
    status VARCHAR(32) NOT NULL,
    error_message TEXT,
    metadata JSONB,
    timestamp TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- =============================================================================
-- IMMUTABILITY ENFORCEMENT TRIGGERS (PostgreSQL 16+)
-- Prevents any UPDATE or DELETE operations on raw_observation and audit_log
-- =============================================================================

CREATE OR REPLACE FUNCTION enforce_immutability()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'FORENSIC_ERROR: Table % is append-only. UPDATE or DELETE operations are strictly prohibited.', TG_TABLE_NAME;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_immutable_raw_observation ON raw_observation;
CREATE TRIGGER trg_immutable_raw_observation
    BEFORE UPDATE OR DELETE ON raw_observation
    FOR EACH ROW EXECUTE FUNCTION enforce_immutability();

DROP TRIGGER IF EXISTS trg_immutable_source_acquisition ON source_acquisition_log;
CREATE TRIGGER trg_immutable_source_acquisition
    BEFORE UPDATE OR DELETE ON source_acquisition_log
    FOR EACH ROW EXECUTE FUNCTION enforce_immutability();

DROP TRIGGER IF EXISTS trg_immutable_audit_log ON audit_log;
CREATE TRIGGER trg_immutable_audit_log
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION enforce_immutability();
