"""
Source Registry Engine.
Enforces authority hierarchy, validates official endpoints,
and prevents calls to unregistered or unverified external sources.
"""
from typing import Dict, List, Optional
from src.core.enums import (
    AuthorityLevel,
    SourceProvider,
    SourceType
)
from src.core.exceptions import (
    UnverifiedSourceError,
    ForensicError
)
from src.db.models import SourceRegistry
from src.db.repository import ProvenanceRepository
from src.engines.registry.seed_sources import CANONICAL_SOURCES


class SourceRegistryEngine:
    def __init__(self, repository: Optional[ProvenanceRepository] = None):
        self.repository = repository
        self._sources: Dict[str, SourceRegistry] = {}
        self.load_seeds()

    def load_seeds(self):
        """Loads canonical sources and registers them into the repository if provided."""
        for src in CANONICAL_SOURCES:
            self._sources[src.source_id] = src
            if self.repository:
                try:
                    self.repository.insert_source(src)
                except Exception:
                    # Ignore duplicate keys when re-initializing in tests
                    pass

    def register_source(self, source: SourceRegistry) -> str:
        """Registers a new validated source."""
        self._sources[source.source_id] = source
        if self.repository:
            self.repository.insert_source(source)
        return source.source_id

    def get_source(self, source_id: str) -> SourceRegistry:
        if source_id not in self._sources:
            raise UnverifiedSourceError(
                f"Source '{source_id}' is not registered in official Source Registry."
            )
        return self._sources[source_id]

    def validate_source_call(self, source_id: str, endpoint: Optional[str] = None) -> SourceRegistry:
        """
        Validates that a source and endpoint comply with authority and registry rules.
        """
        source = self.get_source(source_id)

        # 1. Active status check
        if not source.active:
            raise UnverifiedSourceError(f"Source '{source_id}' is deactivated.")

        # 2. Authority Level Check (Levels 5-7 cannot be used for FACT)
        if not source.authority_level.is_fact_eligible():
            raise ForensicError(
                f"Source '{source_id}' has Authority Level {source.authority_level.value} "
                f"({source.authority_level.name}), which is strictly barred from FACT promotion."
            )

        # 3. Source Type & Endpoint Verification
        if endpoint is not None:
            if source.source_type == SourceType.OFFICIAL_DOWNLOAD:
                raise UnverifiedSourceError(
                    f"Source '{source_id}' is designated as OFFICIAL_DOWNLOAD. "
                    f"Direct API/scraping call to endpoint '{endpoint}' is prohibited."
                )
            if source.api_endpoint and not endpoint.startswith(source.api_endpoint):
                raise UnverifiedSourceError(
                    f"Endpoint mismatch for source '{source_id}'. "
                    f"Expected base '{source.api_endpoint}', but received '{endpoint}'."
                )

        return source

    def list_fact_eligible_sources(self) -> List[SourceRegistry]:
        return [
            src for src in self._sources.values()
            if src.active and src.authority_level.is_fact_eligible()
        ]

    def list_by_provider(self, provider: SourceProvider) -> List[SourceRegistry]:
        return [
            src for src in self._sources.values()
            if src.provider == provider
        ]
