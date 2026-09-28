"""
Validation State Machine.
Enforces the 11-stage data lifecycle:
RAW -> IDENTITY_VALIDATED -> HASH_VERIFIED -> EXTRACTED ->
DERIVED -> COMPOSITE -> VALIDATED -> PIT_COMPLIANT -> PROVISIONAL ->
APPROVED -> PRODUCTION_FACT.
Enforces mandatory human sign-off before APPROVED or PRODUCTION_FACT promotion.
"""
from typing import Optional
from src.core.enums import ValidationStatus
from src.core.exceptions import GateBlockedError, ForensicError

VALID_TRANSITIONS = {
    ValidationStatus.RAW: {ValidationStatus.IDENTITY_VALIDATED, ValidationStatus.BLOCKED, ValidationStatus.INVALID},
    ValidationStatus.IDENTITY_VALIDATED: {ValidationStatus.HASH_VERIFIED, ValidationStatus.BLOCKED, ValidationStatus.CONFLICT},
    ValidationStatus.HASH_VERIFIED: {ValidationStatus.EXTRACTED, ValidationStatus.BLOCKED, ValidationStatus.INVALID},
    ValidationStatus.EXTRACTED: {ValidationStatus.DERIVED, ValidationStatus.VALIDATED, ValidationStatus.BLOCKED},
    ValidationStatus.DERIVED: {ValidationStatus.VALIDATED, ValidationStatus.COMPOSITE, ValidationStatus.BLOCKED},
    ValidationStatus.COMPOSITE: {ValidationStatus.VALIDATED, ValidationStatus.BLOCKED},
    ValidationStatus.VALIDATED: {ValidationStatus.PIT_COMPLIANT, ValidationStatus.BLOCKED, ValidationStatus.LOOKAHEAD_BIAS},
    ValidationStatus.PIT_COMPLIANT: {ValidationStatus.PROVISIONAL, ValidationStatus.BLOCKED},
    ValidationStatus.PROVISIONAL: {ValidationStatus.APPROVED, ValidationStatus.REJECTED, ValidationStatus.BLOCKED},
    ValidationStatus.APPROVED: {ValidationStatus.PRODUCTION_FACT, ValidationStatus.BLOCKED},
    ValidationStatus.PRODUCTION_FACT: set()  # Terminal state
}


class ValidationStateMachine:
    @staticmethod
    def transition(
        current_status: ValidationStatus,
        target_status: ValidationStatus,
        human_approval_token: Optional[str] = None
    ) -> ValidationStatus:
        """
        Transitions status from current to target adhering strictly to transition graph.
        Requires explicit human approval token for APPROVED and PRODUCTION_FACT.
        """
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ForensicError(
                f"Illegal validation transition: Cannot transition from '{current_status.value}' "
                f"to '{target_status.value}'."
            )

        # Gate Rule: Promotion to APPROVED or PRODUCTION_FACT requires explicit human sign-off
        if target_status in (ValidationStatus.APPROVED, ValidationStatus.PRODUCTION_FACT):
            if not human_approval_token or not human_approval_token.startswith("HUMAN_SIGN_OFF_"):
                raise GateBlockedError(
                    f"Promotion to {target_status.value} is strictly BLOCKED. "
                    f"Valid human approval token required (AI cannot self-approve)."
                )

        return target_status
