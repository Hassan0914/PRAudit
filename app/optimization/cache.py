"""Optimization caches for contexts, prompts, and summaries."""

from typing import Any, Dict, Optional
from app.core.logging import setup_logger

logger = setup_logger("optimization.cache")


class ContextCache:
    """Cache storing assembled prompt contexts to prevent redundant generation."""

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self.hits += 1
            logger.debug("ContextCache HIT for key '%s'", key)
            return self._cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value


class PromptCache:
    """Cache storing deduplicated prompt strings."""

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value


class SummaryCache:
    """Cache storing past AI review summaries."""

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value
