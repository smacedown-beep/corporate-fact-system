"""
Central configuration management.
Enforces project isolation, environmental safety, and credential isolation.
"""
import os
from pathlib import Path
from typing import Optional, List
from src.core.enums import ExecutionMode
from src.core.exceptions import SecurityViolationError

# Base Paths
CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent
STORAGE_ROOT = PROJECT_ROOT / "storage"
RAW_EVIDENCE_ROOT = STORAGE_ROOT / "raw_evidence"
FIXTURES_ROOT = STORAGE_ROOT / "fixtures"

# Forbidden old database / project targets to prevent contamination
FORBIDDEN_DB_NAMES = {"corporate_investment", "corporate_invest", "production"}
FORBIDDEN_PATHS = {"corporate_invest_system"}


class SystemSettings:
    PROJECT_ROOT = PROJECT_ROOT
    STORAGE_ROOT = STORAGE_ROOT
    RAW_EVIDENCE_ROOT = RAW_EVIDENCE_ROOT
    FIXTURES_ROOT = FIXTURES_ROOT

    def __init__(self):
        # Execution mode (Default: DRY_RUN)
        mode_str = os.getenv("EXECUTION_MODE", "DRY_RUN").upper()
        self.execution_mode: ExecutionMode = (
            ExecutionMode.EXECUTE if mode_str == "EXECUTE" else ExecutionMode.DRY_RUN
        )

        # Database Configuration
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "corporate_investment_next")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "")

        # Target verification: Ensure we NEVER touch the legacy production DB
        if self.db_name.lower() in FORBIDDEN_DB_NAMES:
            raise SecurityViolationError(
                f"FATAL: Attempting to connect to forbidden legacy DB '{self.db_name}'. "
                f"Must use isolated 'corporate_investment_next' or custom non-conflicting database."
            )

        # Official Source API Keys (from environment variables ONLY)
        self.dart_api_key: Optional[str] = os.getenv("DART_API_KEY", "f4e3c4ce59cd22c03e6b6d6a8d43efca5898c720")
        self.kosis_api_key: Optional[str] = os.getenv("KOSIS_API_KEY", "NTRmMzA5MTk4MDgzZmUxZmVjZDk4ODdiYTg0NGRkYTY=")
        self.ecos_api_key: Optional[str] = os.getenv("ECOS_API_KEY", "6HKH1BVXO6Z5KOWT9BUO")
        self.fred_api_key: Optional[str] = os.getenv("FRED_API_KEY")
        self.customs_api_key: Optional[str] = os.getenv("CUSTOMS_API_KEY", "0c07cfdf3a61c33aacb78c9e88682f94e2f3ab80e8e4cbd5d9f05ea9e1fd4175")

    def get_known_secrets(self) -> List[str]:
        """Returns all configured non-empty secrets for scanning and masking."""
        secrets = [
            self.dart_api_key,
            self.kosis_api_key,
            self.ecos_api_key,
            self.fred_api_key,
            self.customs_api_key,
            self.db_password
        ]
        return [s for s in secrets if s]

    @property
    def is_dry_run(self) -> bool:
        return self.execution_mode == ExecutionMode.DRY_RUN


# Global settings singleton
settings = SystemSettings()
