"""Unit tests for Phase 16: AI Review Engine and Provider Registries."""

from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.registries.model_registry import ModelRegistry
from app.ai.registries.prompt_registry import PromptRegistry
from app.ai.service import AIReviewService


def test_model_registry_pricing() -> None:
    """Test ModelRegistry lookup and cost calculation."""
    registry = ModelRegistry()
    m = registry.get_model("claude-3-5-sonnet")

    assert m.model_id == "claude-3-5-sonnet"
    assert m.provider_name == "anthropic"

    cost = registry.calculate_cost("claude-3-5-sonnet", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0


def test_prompt_registry_templates() -> None:
    """Test PromptRegistry versioned template rendering."""
    registry = PromptRegistry()
    prompt_obj = registry.get_prompt("default-pr-review", "1.0.0")

    assert prompt_obj.version == "1.0.0"
    rendered = registry.render_user_prompt("default-pr-review", "1.0.0", "PR-123", "Sample context", "Sample diff")
    assert "Target PR ID: PR-123" in rendered


def test_ai_review_service_mock_generation() -> None:
    """Test AIReviewService structured JSON review generation."""
    service = AIReviewService(provider=MockLLMProvider())
    review = service.generate_review("PR-MOCK-1", "Sample context", "Sample diff")

    assert review.review_id is not None
    assert review.pr_id == "PR-MOCK-1"
    assert review.summary is not None
    assert len(review.comments) >= 1
    assert len(review.recommendations) >= 1
