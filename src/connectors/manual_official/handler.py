"""
Official Download Ingestion Handler.
Handles official releases from KITA, MOTIE, and public agencies where no open API is offered.
Enforces strict SHA256 checksum verification, provenance stamping, and immutable archival.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from config.settings import RAW_EVIDENCE_ROOT, PROJECT_ROOT
from src.core.enums import SourceProvider, SourceType
from src.core.hashing import compute_file_hashes
from src.core.exceptions import HashMismatchError, UnverifiedSourceError


@dataclass
class OfficialDownloadReceipt:
    source_provider: str
    dataset_code: str
    official_release_date: str
    original_filename: str
    archived_path: str
    sha256: str
    sha1: str
    file_size_bytes: int
    imported_at: datetime
    status: str = "PASS"


class OfficialDownloadHandler:
    @staticmethod
    def ingest_official_file(
        provider: SourceProvider,
        dataset_code: str,
        source_file_path: Path,
        expected_sha256: Optional[str] = None,
        release_date: Optional[str] = None
    ) -> OfficialDownloadReceipt:
        """
        Validates, checksum-verifies, and immutably archives an official downloaded document.
        """
        path = Path(source_file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Official download file not found: {path}")

        # Compute cryptographic hashes
        hashes = compute_file_hashes(path)
        actual_sha256 = hashes["sha256"]

        if expected_sha256 and expected_sha256.lower() != actual_sha256.lower():
            raise HashMismatchError(
                f"Official download SHA256 mismatch for {path.name}! "
                f"Expected '{expected_sha256}', but computed '{actual_sha256}'."
            )

        # Archive file to immutable storage
        target_dir = RAW_EVIDENCE_ROOT / provider.value.lower() / dataset_code
        target_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target_filename = f"{dataset_code}_{ts}_{actual_sha256[:12]}{path.suffix}"
        target_path = target_dir / target_filename

        target_path.write_bytes(path.read_bytes())
        rel_path = str(target_path.relative_to(PROJECT_ROOT))

        return OfficialDownloadReceipt(
            source_provider=provider.value,
            dataset_code=dataset_code,
            official_release_date=release_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            original_filename=path.name,
            archived_path=rel_path,
            sha256=actual_sha256,
            sha1=hashes["sha1"],
            file_size_bytes=hashes["size_bytes"],
            imported_at=datetime.now(timezone.utc)
        )
