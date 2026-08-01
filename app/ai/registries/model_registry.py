"""Model registry storing versioned LLM metadata, token limits, and pricing rates."""

from dataclasses import dataclass
from typing import Dict, Optional
from app.core.exceptions import PRAuditError
from app.core.logging import setup_logger

logger = setup_logger("ai.model_registry")


@dataclass
class ModelMetadata:
    """Metadata specification for a versioned LLM model."""

    model_id: str
    provider_name: str
    max_context_tokens: int
    max_output_tokens: int
    input_cost_per_1m: float   # USD cost per 1M input tokens
    output_cost_per_1m: float  # USD cost per 1M output tokens
    supports_structured_json: bool = True


class ModelRegistry:
    """Registry maintaining available LLM model metadata and pricing formulas."""

    def __init__(self) -> None:
        """Initialize ModelRegistry with standard industry models."""
        self._models: Dict[str, ModelMetadata] = {}
        self._register_default_models()

    def _register_default_models(self) -> None:
        """Register default supported LLM models and current pricing rates."""
        defaults = [
            ModelMetadata(
                model_id="claude-3-5-sonnet",
                provider_name="anthropic",
                max_context_tokens=200000,
                max_output_tokens=8192,
                input_cost_per_1m=3.00,
                output_cost_per_1m=15.00,
            ),
            ModelMetadata(
                model_id="gpt-4o",
                provider_name="openai",
                max_context_tokens=128000,
                max_output_tokens=4096,
                input_cost_per_1m=2.50,
                output_cost_per_1m=10.00,
            ),
            ModelMetadata(
                model_id="gemini-1.5-pro",
                provider_name="gemini",
                max_context_tokens=1000000,
                max_output_tokens=8192,
                input_cost_per_1m=3.50,
                output_cost_per_1m=10.50,
            ),
            ModelMetadata(
                model_id="ollama-llama3",
                provider_name="ollama",
                max_context_tokens=8192,
                max_output_tokens=2048,
                input_cost_per_1m=0.0,
                output_cost_per_1m=0.0,
            ),
            ModelMetadata(
                model_id="mock-model",
                provider_name="mock",
                max_context_tokens=100000,
                max_output_tokens=4096,
                input_cost_per_1m=0.0,
                output_cost_per_1m=0.0,
            ),
        ]
        for m in defaults:
            self._models[m.model_id] = m

    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a new or custom model definition."""
        self._models[metadata.model_id] = metadata
        logger.info("Registered model '%s' under provider '%s'", metadata.model_id, metadata.provider_name)

    def get_model(self, model_id: str) -> ModelMetadata:
        """Retrieve ModelMetadata by model ID string.

        Args:
            model_id: Target model identifier.

        Returns:
            ModelMetadata object.
        """
        if model_id not in self._models:
            logger.warning("Model '%s' not registered. Falling back to 'mock-model'", model_id)
            return self._models.get("mock-model", ModelMetadata("mock-model", "mock", 100000, 4096, 0.0, 0.0))
        return self._models[model_id]

    def calculate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate total USD cost for a model execution based on token counts.

        Args:
            model_id: Model ID string.
            prompt_tokens: Number of prompt/input tokens.
            completion_tokens: Number of output/completion tokens.

        Returns:
            Estimated USD cost.
        """
        model = self.get_model(model_id)
        input_cost = (prompt_tokens / 1_000_000.0) * model.input_cost_per_1m
        output_cost = (completion_tokens / 1_000_000.0) * model.output_cost_per_1m
        return round(input_cost + output_cost, 6)
