"""Base agent class with shared utilities."""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from core.cache import cache
from core.models import ResearchRequest, ResearchResult
from scraping.client import PoliteClient, create_client


class BaseAgent(ABC):
    """All agents inherit from BaseAgent for caching and HTTP access."""

    name: str = "base"

    def __init__(self, client: PoliteClient | None = None):
        self.client = client or create_client()
        self.agent_id = str(uuid.uuid4())[:8]

    def _cache_key(self, *parts: str) -> str:
        return ":".join([self.name, *parts])

    def cached_get(
        self,
        namespace: str,
        identifier: str,
        fetch_fn,
        ttl_seconds: int | None = None,
    ) -> Any:
        key = self._cache_key(namespace, identifier)
        cached = cache.get(self.name, key)
        if cached is not None:
            return cached
        value = fetch_fn()
        cache.set(self.name, key, value, ttl_seconds=ttl_seconds)
        return value

    @abstractmethod
    def run(self, request: ResearchRequest) -> Any:
        ...
