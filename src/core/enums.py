"""
Core enumeration types for the Corporate Investment FACT & Provenance System.
Defines authoritative levels, validation states, forensic verdicts, and gate states.
"""
from enum import Enum, IntEnum


class AuthorityLevel(IntEnum):
    """
    Data source authority hierarchy.
    Levels 5-7 are strictly prohibited from being promoted to FACT.
    """
    LEVEL_1_GOV_PUBLIC = 1        # Official Government / Public Authority
    LEVEL_2_OFFICIAL_FILING = 2   # Official Corporate Filing / IR (DART)
    LEVEL_3_OFFICIAL_STAT = 3     # Official Association / Official Statistical Organization
    LEVEL_4_INTERNATIONAL = 4     # International Official Dataset (FRED, etc.)
    LEVEL_5_SECONDARY = 5         # Secondary Research (NOT FACT)
    LEVEL_6_NEWS = 6              # News / Media (NOT FACT)
    LEVEL_7_AI = 7                # AI Generated (NOT FACT)

    def is_fact_eligible(self) -> bool:
        return self.value in (1, 2, 3, 4)


class SourceProvider(str, Enum):
    DART = "DART"
    KOSIS = "KOSIS"
    ECOS = "ECOS"
    FRED = "FRED"
    CUSTOMS = "CUSTOMS"
    KITA = "KITA"
    MOTIE = "MOTIE"


class SourceType(str, Enum):
    API = "API"
    OFFICIAL_DOWNLOAD = "OFFICIAL_DOWNLOAD"
    MANUAL_IMPORT = "MANUAL_IMPORT"


class ValidationStatus(str, Enum):
    """
    Strict status machine.
    """
    RAW = "RAW"
    IDENTITY_VALIDATED = "IDENTITY_VALIDATED"
    HASH_VERIFIED = "HASH_VERIFIED"
    EXTRACTED = "EXTRACTED"
    DERIVED = "DERIVED"
    COMPOSITE = "COMPOSITE"
    VALIDATED = "VALIDATED"
    PIT_COMPLIANT = "PIT_COMPLIANT"
    PROVISIONAL = "PROVISIONAL"
    APPROVED = "APPROVED"
    PRODUCTION_FACT = "PRODUCTION_FACT"

    # Exception and Halt states
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"
    CONFLICT = "CONFLICT"
    INVALID = "INVALID"
    CONTAMINATED = "CONTAMINATED"
    REJECTED = "REJECTED"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    LOOKAHEAD_BIAS = "LOOKAHEAD_BIAS"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class ForensicVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


class GateState(str, Enum):
    STOP = "STOP"
    OPEN = "OPEN"


class ExecutionMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    EXECUTE = "EXECUTE"
