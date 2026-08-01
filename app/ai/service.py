"""AI Review Service orchestrating LLM provider execution and structured reviews."""

import hashlib
import json
import time
from typing import Any, Dict, Optional

from app.ai.models import (
    AIComment,
    AIPriority,
    AIRecommendation,
    AIRiskAssessment,
    AIReview,
    RiskLevel,
)
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.registries.model_registry import ModelRegistry
from app.ai.registries.prompt_registry import PromptRegistry
from app.core.logging import setup_logger

logger = setup_logger("ai.service")


class AIReviewService:
    """Service providing AI-augmented code review generation using versioned registries and pluggable providers."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model_registry: Optional[ModelRegistry] = None,
        prompt_registry: Optional[PromptRegistry] = None,
    ) -> None:
        """Initialize AIReviewService."""
        self.provider = provider or MockLLMProvider()
        self.model_registry = model_registry or ModelRegistry()
        self.prompt_registry = prompt_registry or PromptRegistry()

    def generate_review(
        self,
        pr_id: str,
        context_text: str,
        diff_text: str,
        model_id: Optional[str] = None,
        prompt_name: str = "default-pr-review",
        prompt_version: str = "1.0.0",
    ) -> AIReview:
        """Generate AI-augmented Pull Request review.

        Args:
            pr_id: Target Pull Request ID.
            context_text: Assembled context from deterministic analysis engines.
            diff_text: Pull Request diff text.
            model_id: Target LLM model ID.
            prompt_name: Prompt name in PromptRegistry.
            prompt_version: Prompt version in PromptRegistry.

        Returns:
            AIReview object.
        """
        review_id = hashlib.sha256(f"aireview:{pr_id}:{time.time()}".encode()).hexdigest()[:16]
        target_model = model_id or self.provider.default_model_id

        logger.info(
            "Executing AI Review for PR %s (Review ID: %s, Provider: %s, Model: %s)",
            pr_id,
            review_id,
            self.provider.provider_name,
            target_model,
        )

        prompt_obj = self.prompt_registry.get_prompt(prompt_name, prompt_version)
        rendered_user_prompt = self.prompt_registry.render_user_prompt(
            prompt_name, prompt_version, pr_id, context_text, diff_text
        )

        output_payload = self.provider.generate_review(
            system_prompt=prompt_obj.system_prompt,
            user_prompt=rendered_user_prompt,
            model_id=target_model,
        )

        raw_text = output_payload.get("raw_text", "{}")
        p_tokens = output_payload.get("prompt_tokens", 0)
        c_tokens = output_payload.get("completion_tokens", 0)
        tot_tokens = p_tokens + c_tokens

        cost_usd = self.model_registry.calculate_cost(target_model, p_tokens, c_tokens)

        # Parse structured JSON payload
        parsed_data = self._parse_json_payload(raw_text)

        summary_str = parsed_data.get("summary", "AI Review completed.")
        risk_data = parsed_data.get("risk_assessment", {})
        risk_obj = AIRiskAssessment(
            overall_risk_score=risk_data.get("overall_risk_score", 20),
            risk_level=RiskLevel(risk_data.get("risk_level", "LOW")),
            key_risks=risk_data.get("key_risks", []),
            architectural_impact=risk_data.get("architectural_impact", "Low"),
            testing_gaps=risk_data.get("testing_gaps", []),
        )

        comments: list[AIComment] = []
        for c in parsed_data.get("comments", []):
            comments.append(
                AIComment(
                    file_path=c.get("file_path", "src/file.py"),
                    line=c.get("line", 1),
                    side=c.get("side", "RIGHT"),
                    title=c.get("title", "Review Note"),
                    explanation=c.get("explanation", ""),
                    suggestion=c.get("suggestion"),
                    priority=AIPriority(c.get("priority", "MEDIUM")),
                    category=c.get("category", "General"),
                )
            )

        recommendations: list[AIRecommendation] = []
        for r in parsed_data.get("recommendations", []):
            recommendations.append(
                AIRecommendation(
                    topic=r.get("topic", "Recommendation"),
                    category=r.get("category", "Quality"),
                    action_item=r.get("action_item", ""),
                    code_example=r.get("code_example"),
                    priority=AIPriority(r.get("priority", "LOW")),
                )
            )

        return AIReview(
            review_id=review_id,
            pr_id=pr_id,
            summary=summary_str,
            risk_assessment=risk_obj,
            comments=comments,
            recommendations=recommendations,
            total_tokens_used=tot_tokens,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            estimated_cost_usd=cost_usd,
            provider_name=self.provider.provider_name,
            model_name=target_model,
        )

    def _parse_json_payload(self, text: str) -> Dict[str, Any]:
        """Safely parse LLM raw text into dictionary payload."""
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as exc:
            logger.warning("Failed to parse LLM response as JSON: %s", exc)
            return {
                "summary": "AI Review generated (raw text output).",
                "risk_assessment": {"overall_risk_score": 10, "risk_level": "LOW"},
                "comments": [],
                "recommendations": [],
            }
