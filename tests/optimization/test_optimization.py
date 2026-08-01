"""Unit tests for Phase 29: AI Cost Optimization Engine."""

from app.optimization.optimizer import CostOptimizer


def test_cost_optimizer() -> None:
    optimizer = CostOptimizer()
    opt_text = optimizer.optimize_context("key1", "Sample   raw    prompt   text.\n\n\nMore text.")

    assert "Sample" in opt_text and "More text." in opt_text

    # Test cache hit
    opt_text_cached = optimizer.optimize_context("key1", "Sample   raw    prompt   text.\n\n\nMore text.")
    assert opt_text_cached == opt_text

    metrics = optimizer.get_optimization_metrics()
    assert metrics.cache_hit_rate > 0.0
    assert metrics.total_tokens_saved > 0
