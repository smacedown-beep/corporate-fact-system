"""
Provider-specific rate limiting and retry configuration.
Ensures strict compliance with official API guidelines and prevents rate limit loops.
"""
from dataclasses import dataclass
from typing import Dict
from src.core.enums import SourceProvider


@dataclass(frozen=True)
class RateLimitConfig:
    max_requests_per_window: int
    window_seconds: int
    max_retries: int
    base_backoff_seconds: float
    max_backoff_seconds: float


# Default configurations per provider based on official documentation
PROVIDER_RATE_LIMITS: Dict[SourceProvider, RateLimitConfig] = {
    SourceProvider.DART: RateLimitConfig(
        max_requests_per_window=100,
        window_seconds=60,
        max_retries=3,
        base_backoff_seconds=2.0,
        max_backoff_seconds=30.0,
    ),
    SourceProvider.KOSIS: RateLimitConfig(
        max_requests_per_window=60,
        window_seconds=60,
        max_retries=3,
        base_backoff_seconds=1.5,
        max_backoff_seconds=20.0,
    ),
    SourceProvider.ECOS: RateLimitConfig(
        max_requests_per_window=100,
        window_seconds=60,
        max_retries=3,
        base_backoff_seconds=1.0,
        max_backoff_seconds=15.0,
    ),
    SourceProvider.FRED: RateLimitConfig(
        max_requests_per_window=120,
        window_seconds=60,
        max_retries=3,
        base_backoff_seconds=1.0,
        max_backoff_seconds=20.0,
    ),
    SourceProvider.CUSTOMS: RateLimitConfig(
        max_requests_per_window=30,
        window_seconds=60,
        max_retries=2,
        base_backoff_seconds=3.0,
        max_backoff_seconds=30.0,
    ),
}
