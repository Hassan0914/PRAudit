"""OpenAI LLM provider implementation with graceful fallback."""

import os
from typing import Any, Dict, Optional
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.logging import setup_logger

logger = setup_logger("ai.providers.openai")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4o LLM provider."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.fallback = MockLLMProvider()

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model_id(self) -> str:
        return "gpt-4o"

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        target_model = model_id or self.default_model_id
        if not self.api_key:
            logger.info("No OPENAI_API_KEY set. Falling back to MockLLMProvider.")
            res = self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
            res["model_id"] = target_model
            return res

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            resp = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw_text = resp.choices[0].message.content or ""
            p_tokens = resp.usage.prompt_tokens if resp.usage else 0
            c_tokens = resp.usage.completion_tokens if resp.usage else 0

            return {
                "raw_text": raw_text,
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "model_id": target_model,
            }
        except Exception as exc:
            logger.error("OpenAI API call failed: %s. Using fallback mock.", exc)
            return self.fallback.generate_review(system_prompt, user_prompt, target_model, max_tokens)
