"""Anthropic Claude LLM provider implementation with graceful fallback."""

import os
from typing import Any, Dict, Optional
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.logging import setup_logger

logger = setup_logger("ai.providers.anthropic")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.fallback = MockLLMProvider()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def default_model_id(self) -> str:
        return "claude-3-5-sonnet"

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        target_model = model_id or self.default_model_id
        if not self.api_key:
            logger.info("No ANTHROPIC_API_KEY set. Falling back to MockLLMProvider.")
            res = self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
            res["model_id"] = target_model
            return res

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            msg = client.messages.create(
                model=target_model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = msg.content[0].text
            p_tokens = msg.usage.input_tokens
            c_tokens = msg.usage.output_tokens

            return {
                "raw_text": raw_text,
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "model_id": target_model,
            }
        except Exception as exc:
            logger.error("Anthropic API call failed: %s. Using fallback mock.", exc)
            return self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
