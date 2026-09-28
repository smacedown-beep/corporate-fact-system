"""
Derivation Calculation and Lineage Stamping Engine.
Calculates Derived and Composite metrics, automatically inheriting the
latest availability_date and recording data lineage links.
"""
from typing import List, Dict, Any, Union, Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from src.db.models import (
    RawObservation,
    DerivedObservation,
    CompositeIndicator,
    DataLineage
)
from src.db.repository import ProvenanceRepository
from src.core.enums import ValidationStatus


class DerivationEngine:
    def __init__(self, repository: ProvenanceRepository):
        self.repository = repository
        self.software_version = "0.1.0"

    def compute_derived_metric(
        self,
        metric_name: str,
        derived_value: Decimal,
        unit: str,
        formula: str,
        parent_observations: List[Union[RawObservation, DerivedObservation]],
        company_id: Optional[str] = None,
        calculation_version: str = "v1.0"
    ) -> DerivedObservation:
        """
        Creates a DerivedObservation and writes lineage links to all parents.
        Availability date is strictly computed as max(parent.availability_date).
        """
        if not parent_observations:
            raise ValueError("Derived metric requires at least one parent observation.")

        # PIT Rule: Derived metric cannot be available earlier than its latest input
        max_avail = max(p.availability_date for p in parent_observations)

        derived_id = str(uuid.uuid4())
        derived = DerivedObservation(
            derived_id=derived_id,
            company_id=company_id,
            metric_name=metric_name,
            derived_value=derived_value,
            unit=unit,
            formula=formula,
            calculation_version=calculation_version,
            calculated_at=datetime.now(timezone.utc),
            availability_date=max_avail,
            validation_status=ValidationStatus.DERIVED
        )
        self.repository.insert_derived_observation(derived)

        # Record lineage links to all parents
        for p in parent_observations:
            parent_type = "RAW" if isinstance(p, RawObservation) else "DERIVED"
            parent_id = p.raw_id if isinstance(p, RawObservation) else p.derived_id
            lineage = DataLineage(
                parent_entity_type=parent_type,
                parent_id=parent_id,
                child_entity_type="DERIVED",
                child_id=derived_id,
                transformation_rule=formula,
                software_version=self.software_version
            )
            self.repository.insert_lineage(lineage)

        return derived

    def compute_composite_indicator(
        self,
        indicator_name: str,
        composite_value: Decimal,
        components_spec: Dict[str, Any],
        formula: str,
        parent_observations: List[Union[RawObservation, DerivedObservation]],
    ) -> CompositeIndicator:
        """
        Creates a CompositeIndicator and records complete multi-source lineage.
        """
        max_avail = max(p.availability_date for p in parent_observations)
        composite_id = str(uuid.uuid4())

        composite = CompositeIndicator(
            composite_id=composite_id,
            indicator_name=indicator_name,
            composite_value=composite_value,
            components_spec=components_spec,
            formula=formula,
            availability_date=max_avail,
            validation_status=ValidationStatus.COMPOSITE
        )
        # Note: Composite storage via direct SQL or repository
        sql = """
        INSERT INTO composite_indicator (
            composite_id, indicator_name, composite_value, components_spec,
            formula, availability_date, validation_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        import json
        params = (
            composite.composite_id, composite.indicator_name, float(composite.composite_value),
            json.dumps(composite.components_spec), composite.formula,
            composite.availability_date.isoformat(), composite.validation_status.value,
            composite.created_at.isoformat()
        )
        self.repository.engine.execute_write(sql, params)

        # Link lineage to all components
        for p in parent_observations:
            parent_type = "RAW" if isinstance(p, RawObservation) else "DERIVED"
            parent_id = p.raw_id if isinstance(p, RawObservation) else p.derived_id
            lineage = DataLineage(
                parent_entity_type=parent_type,
                parent_id=parent_id,
                child_entity_type="COMPOSITE",
                child_id=composite_id,
                transformation_rule=f"Composite component in {indicator_name}",
                software_version=self.software_version
            )
            self.repository.insert_lineage(lineage)

        return composite
