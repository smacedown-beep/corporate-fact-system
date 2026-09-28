"""
Standard exception hierarchy for forensic, provenance, security, and gate violations.
"""

class ProvenanceSystemError(Exception):
    """Base exception for all system errors."""
    pass


class SecurityViolationError(ProvenanceSystemError):
    """Raised when an attempt to log, expose, or hardcode credentials occurs."""
    pass


class GateBlockedError(ProvenanceSystemError):
    """Raised when a write, canonical update, or migration is attempted while gate is STOP."""
    pass


class ForensicError(ProvenanceSystemError):
    """Base exception for forensic validation failures."""
    pass


class IdentityMismatchError(ForensicError):
    """Raised when corp_code, stock_code, or company name does not match expected identity."""
    pass


class ContaminationError(ForensicError):
    """Raised when cross-company data contamination is detected in the pipeline."""
    pass


class HashMismatchError(ForensicError):
    """Raised when byte stream or file hash does not match recorded SHA256/SHA1."""
    pass


class ProvenanceMissingError(ForensicError):
    """Raised when an observation or metric lacks verifiable lineage to raw evidence."""
    pass


class LookaheadBiasError(ForensicError):
    """Raised when availability_date is after decision_date in Point-in-Time analysis."""
    pass


class UnverifiedSourceError(ProvenanceSystemError):
    """Raised when an unregistered or unverified source endpoint is invoked."""
    pass
