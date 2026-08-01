"""Abstract LLM Provider interface allowing provider swapping without changing business logic."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.ai.models import AIReview


class LLMProvider(ABC):
    """Abstract base class for all LLM providers (Anthropic, OpenAI, Gemini, Ollama, Mock)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name string identifier."""
        pass

    @property
    @abstractmethod
    def default_model_id(self) -> str:
        """Default model ID for this provider."""
        pass

    @abstractmethod
    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Generate structured LLM response payload.

        Args:
            system_prompt: System prompt text instructions.
            user_prompt: Rendered user prompt text context.
            model_id: Target model ID string.
            max_tokens: Maximum output token limit.

        Returns:
            Dictionary payload containing 'raw_text', 'prompt_tokens', 'completion_tokens', 'model_id'.
        """
        pass
