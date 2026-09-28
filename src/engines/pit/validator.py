"""
Point-in-Time (PIT) Compliance and Lookahead Bias Protection Engine.
Strictly verifies that no future information is leaked into past investment decisions.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from src.core.exceptions import LookaheadBiasError
from src.core.enums import ValidationStatus


@dataclass
class PitCheckResult:
    is_pit_valid: bool
    decision_date: datetime
    availability_date: datetime
    status: ValidationStatus
    reason: str


class PitValidator:
    @staticmethod
    def validate_pit(
        decision_date: datetime,
        availability_date: datetime,
        metric_name: str = "observation"
    ) -> PitCheckResult:
        """
        Validates: availability_date <= decision_date.
        If availability_date > decision_date, flags LOOKAHEAD_BIAS.
        """
        if decision_date.tzinfo is None:
            decision_date = decision_date.replace(tzinfo=timezone.utc)
        if availability_date.tzinfo is None:
            availability_date = availability_date.replace(tzinfo=timezone.utc)

        if availability_date > decision_date:
            return PitCheckResult(
                is_pit_valid=False,
                decision_date=decision_date,
                availability_date=availability_date,
                status=ValidationStatus.LOOKAHEAD_BIAS,
                reason=(
                    f"LOOKAHEAD_BIAS detected in '{metric_name}': "
                    f"Data became available on {availability_date.isoformat()}, "
                    f"which is AFTER the decision date {decision_date.isoformat()}."
                )
            )

        return PitCheckResult(
            is_pit_valid=True,
            decision_date=decision_date,
            availability_date=availability_date,
            status=ValidationStatus.PIT_COMPLIANT,
            reason="Point-in-Time compliant."
        )

    @classmethod
    def assert_pit_compliant(
        cls,
        decision_date: datetime,
        availability_date: datetime,
        metric_name: str = "observation"
    ):
        result = cls.validate_pit(decision_date, availability_date, metric_name)
        if not result.is_pit_valid:
            raise LookaheadBiasError(result.reason)
