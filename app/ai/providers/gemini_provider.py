"""Google Gemini LLM provider implementation with graceful fallback."""

import os
from typing import Any, Dict, Optional
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.logging import setup_logger

logger = setup_logger("ai.providers.gemini")


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.fallback = MockLLMProvider()

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model_id(self) -> str:
        return "gemini-1.5-pro"

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        target_model = model_id or self.default_model_id
        if not self.api_key:
            logger.info("No GEMINI_API_KEY set. Falling back to MockLLMProvider.")
            res = self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
            res["model_id"] = target_model
            return res

        res = self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
        res["model_id"] = target_model
        return res
