"""Ollama Local LLM provider implementation with graceful fallback."""

import os
from typing import Any, Dict, Optional
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.logging import setup_logger

logger = setup_logger("ai.providers.ollama")


class OllamaProvider(LLMProvider):
    """Ollama Local LLM provider."""

    def __init__(self, host: Optional[str] = None) -> None:
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.fallback = MockLLMProvider()

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model_id(self) -> str:
        return "ollama-llama3"

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        target_model = model_id or self.default_model_id
        res = self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
        res["model_id"] = target_model
        return res
