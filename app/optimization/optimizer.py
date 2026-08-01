"""Prompt and Cost Optimizer calculating cache hit metrics and USD savings."""

from dataclasses import dataclass
from typing import Dict, Optional
from app.core.logging import setup_logger
from app.optimization.cache import ContextCache, PromptCache, SummaryCache
from app.optimization.compression import CompressionService

logger = setup_logger("optimization.optimizer")


@dataclass
class OptimizationMetrics:
    """Metrics container tracking cost savings and token reductions."""

    cache_hit_rate: float
    total_tokens_saved: int
    estimated_usd_saved: float
    compressed_contexts_count: int


class CostOptimizer:
    """Master optimizer managing prompt caches, compression, and cost metrics."""

    def __init__(self) -> None:
        self.context_cache = ContextCache()
        self.prompt_cache = PromptCache()
        self.summary_cache = SummaryCache()
        self.compression = CompressionService()

        self.tokens_saved = 0
        self.compressed_count = 0

    def optimize_context(self, context_key: str, raw_text: str) -> str:
        """Compress and cache context text.

        Args:
            context_key: Cache lookup key string.
            raw_text: Raw context text string.

        Returns:
            Optimized text string.
        """
        cached = self.context_cache.get(context_key)
        if cached:
            saved_tokens = len(raw_text.split())
            self.tokens_saved += saved_tokens
            return cached

        compressed = self.compression.compress_text(raw_text)
        self.context_cache.set(context_key, compressed)
        self.compressed_count += 1
        return compressed

    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Get aggregate optimization and USD cost savings report."""
        total_accesses = self.context_cache.hits + self.context_cache.misses
        hit_rate = round(self.context_cache.hits / total_accesses, 4) if total_accesses > 0 else 0.0

        # Estimated savings: $3.00 per 1M input tokens
        usd_saved = round((self.tokens_saved / 1_000_000.0) * 3.00, 6)

        return OptimizationMetrics(
            cache_hit_rate=hit_rate,
            total_tokens_saved=self.tokens_saved,
            estimated_usd_saved=usd_saved,
            compressed_contexts_count=self.compressed_count,
        )
