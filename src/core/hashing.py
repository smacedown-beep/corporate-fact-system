"""
Dual hashing (SHA-256 and SHA-1) and immutable evidence integrity engine.
All raw evidence files and API responses are hashed for non-repudiation.
"""
import hashlib
from pathlib import Path
from typing import Tuple, Union, Dict, Any


def compute_hashes(data: Union[bytes, str]) -> Dict[str, str]:
    """
    Computes both SHA256 and SHA1 for given bytes or text.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    
    sha256 = hashlib.sha256(data).hexdigest()
    sha1 = hashlib.sha1(data).hexdigest()
    return {
        "sha256": sha256,
        "sha1": sha1,
        "size_bytes": len(data)
    }


def compute_file_hashes(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Computes both SHA256 and SHA1 for a file in chunks to handle large documents.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Evidence file not found: {path}")

    h_sha256 = hashlib.sha256()
    h_sha1 = hashlib.sha1()
    total_bytes = 0

    with path.open("rb") as f:
        while chunk := f.read(65536):
            h_sha256.update(chunk)
            h_sha1.update(chunk)
            total_bytes += len(chunk)

    return {
        "sha256": h_sha256.hexdigest(),
        "sha1": h_sha1.hexdigest(),
        "size_bytes": total_bytes
    }


def verify_file_integrity(
    file_path: Union[str, Path],
    expected_sha256: str,
    expected_sha1: str = None
) -> bool:
    """
    Verifies that the file matches the expected cryptographic hashes.
    """
    hashes = compute_file_hashes(file_path)
    if hashes["sha256"].lower() != expected_sha256.lower():
        return False
    if expected_sha1 and hashes["sha1"].lower() != expected_sha1.lower():
        return False
    return True
