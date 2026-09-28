"""
Governance and Execution Gates.
Enforces hard-stop policies for Database Writes, Canonical Modifications, and Migrations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.core.enums import GateState, ExecutionMode
from src.core.exceptions import GateBlockedError


@dataclass
class GateCheckResult:
    is_open: bool
    reasons: List[str] = field(default_factory=list)
    pending_conditions: List[str] = field(default_factory=list)


class DbWriteGate:
    """
    Controls writing to the database. Defaults to DRY_RUN / STOP.
    """
    def __init__(self, mode: ExecutionMode = ExecutionMode.DRY_RUN):
        self.mode = mode
        self.state = GateState.STOP if mode == ExecutionMode.DRY_RUN else GateState.OPEN

    def set_mode(self, mode: ExecutionMode):
        self.mode = mode
        self.state = GateState.OPEN if mode == ExecutionMode.EXECUTE else GateState.STOP

    def assert_can_write(self, operation_desc: str = "DB Write"):
        if self.state != GateState.OPEN or self.mode != ExecutionMode.EXECUTE:
            raise GateBlockedError(
                f"[DB_WRITE_GATE: STOP] Cannot execute '{operation_desc}'. "
                f"Current mode is {self.mode.value}. Explicit '--execute' flag is required."
            )


class CanonicalWriteGate:
    """
    Controls updates to canonical reference data.
    Requires 7 mandatory verifications + explicit human approval.
    """
    REQUIRED_CHECKS = [
        "official_source_verified",
        "identity_verified",
        "raw_hash_verified",
        "extraction_verified",
        "calculation_verified",
        "lineage_verified",
        "human_approval"
    ]

    @classmethod
    def evaluate(cls, verification_status: Dict[str, bool]) -> GateCheckResult:
        pending = []
        for req in cls.REQUIRED_CHECKS:
            if not verification_status.get(req, False):
                pending.append(req)

        if pending:
            return GateCheckResult(
                is_open=False,
                reasons=[f"Missing mandatory verification: {item}" for item in pending],
                pending_conditions=pending
            )
        return GateCheckResult(is_open=True, reasons=["All canonical verifications satisfied."])

    @classmethod
    def assert_can_write_canonical(cls, verification_status: Dict[str, bool]):
        result = cls.evaluate(verification_status)
        if not result.is_open:
            raise GateBlockedError(
                f"[CANONICAL_WRITE_GATE: STOP] Modifications blocked. Pending: {', '.join(result.pending_conditions)}"
            )


class MigrationGate:
    """
    Controls final migration from forensic staging to production canonical.
    Initial state is strictly STOP.
    Requires 8 mandatory gates including human approval.
    """
    REQUIRED_GATES = [
        "source_completeness",
        "identity_validation",
        "provenance_validation",
        "eps_validation",
        "db_contamination_review",
        "canonical_reconciliation",
        "tests_passed",
        "human_approval"
    ]

    @classmethod
    def evaluate(cls, gate_statuses: Dict[str, bool]) -> GateCheckResult:
        pending = []
        for req in cls.REQUIRED_GATES:
            if not gate_statuses.get(req, False):
                pending.append(req)

        if pending:
            return GateCheckResult(
                is_open=False,
                reasons=[f"Unmet migration gate requirement: {item}" for item in pending],
                pending_conditions=pending
            )
        return GateCheckResult(is_open=True, reasons=["All 8 migration requirements satisfied."])

    @classmethod
    def assert_can_migrate(cls, gate_statuses: Dict[str, bool]):
        result = cls.evaluate(gate_statuses)
        if not result.is_open:
            raise GateBlockedError(
                f"[MIGRATION_GATE: STOP] Migration blocked. Unmet gates: {', '.join(result.pending_conditions)}"
            )
