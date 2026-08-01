"""Review Cache Service providing in-memory and Redis review caching."""

from typing import Any, Dict, Optional
from app.core.logging import setup_logger

logger = setup_logger("cache.service")


class ReviewCacheService:
    """Service providing fast review result caching."""

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached review or context entry."""
        val = self._cache.get(key)
        if val:
            logger.debug("Cache HIT for key '%s'", key)
        return val

    def set(self, key: str, value: Any) -> None:
        """Store entry in cache."""
        self._cache[key] = value
        logger.debug("Cache STORED for key '%s'", key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared.")
