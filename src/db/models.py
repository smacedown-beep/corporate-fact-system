"""
Data Models for all 10 Core Tables.
Provides strong typing, validation, and serialization.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid
from decimal import Decimal

from src.core.enums import (
    AuthorityLevel,
    SourceProvider,
    SourceType,
    ValidationStatus
)


@dataclass
class CompanyMaster:
    company_name: str
    corp_code: str
    stock_code: Optional[str] = None
    company_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name_en: Optional[str] = None
    market: Optional[str] = None
    country: str = "KR"
    industry_code: Optional[str] = None
    industry_name: Optional[str] = None
    status: str = "ACTIVE"
    effective_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    effective_to: Optional[datetime] = None


@dataclass
class SourceRegistry:
    source_id: str
    provider: SourceProvider
    source_name: str
    source_type: SourceType
    authority_level: AuthorityLevel
    official_url: str
    authentication_type: str
    api_endpoint: Optional[str] = None
    api_key_env: Optional[str] = None
    dataset_code: Optional[str] = None
    table_code: Optional[str] = None
    series_code: Optional[str] = None
    unit: Optional[str] = None
    frequency: Optional[str] = None
    availability_rule: Optional[str] = None
    active: bool = True
    last_verified_at: Optional[datetime] = None


@dataclass
class SourceAcquisitionLog:
    source_id: str
    endpoint: str
    http_method: str
    request_parameters_hash: str
    http_status: int
    response_sha256: str
    response_sha1: str
    raw_storage_path: str
    file_size_bytes: int
    parser_version: str
    acquisition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    acquired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RawObservation:
    acquisition_id: str
    observation_period: str
    source_update_date: datetime
    availability_date: datetime
    raw_metric_name: str
    raw_value_text: str
    unit: str
    raw_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None
    entity_identity_hash: Optional[str] = None
    source_record_identifier: Optional[str] = None  # e.g., rcept_no
    raw_value_numeric: Optional[Decimal] = None
    source_location_metadata: Optional[Dict[str, Any]] = None
    validation_status: ValidationStatus = ValidationStatus.RAW
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DerivedObservation:
    metric_name: str
    derived_value: Decimal
    unit: str
    formula: str
    calculation_version: str
    availability_date: datetime
    derived_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validation_status: ValidationStatus = ValidationStatus.DERIVED


@dataclass
class CompositeIndicator:
    indicator_name: str
    composite_value: Decimal
    components_spec: Dict[str, Any]
    formula: str
    availability_date: datetime
    composite_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    validation_status: ValidationStatus = ValidationStatus.COMPOSITE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DataLineage:
    parent_entity_type: str  # RAW, DERIVED, COMPOSITE
    parent_id: str
    child_entity_type: str   # DERIVED, COMPOSITE, PRODUCTION_FACT
    child_id: str
    software_version: str
    transformation_rule: Optional[str] = None
    lineage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ForensicEvidence:
    target_type: str  # RECEIPT, EPS, TAXONOMY, METRIC
    detected_issue: str
    expected_identity: Dict[str, Any]
    actual_identity: Dict[str, Any]
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_identifier: Optional[str] = None
    raw_evidence_hash: Optional[str] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "BLOCKED"


@dataclass
class CanonicalReconciliation:
    company_id: str
    metric_name: str
    period: str
    canonical_value: Optional[Decimal] = None
    official_value: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    receipt_match: Optional[bool] = None
    identity_match: Optional[bool] = None
    provenance_status: Optional[str] = None
    reconciliation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reconciled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AuditLog:
    actor: str
    operation: str
    status: str
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: Optional[str] = None
    record_id: Optional[str] = None
    before_hash: Optional[str] = None
    after_hash: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
