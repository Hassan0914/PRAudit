"""Mock LLM Provider for offline testing, benchmarks, and fallback execution."""

import json
from typing import Any, Dict, Optional
from app.ai.providers.base import LLMProvider
from app.core.logging import setup_logger

logger = setup_logger("ai.providers.mock")


class MockLLMProvider(LLMProvider):
    """Mock LLM provider generating valid structured JSON responses."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model_id(self) -> str:
        return "mock-model"

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Generate mock structured review response."""
        target_model = model_id or self.default_model_id
        logger.debug("Generating mock LLM review output for model '%s'", target_model)

        mock_json = {
            "summary": "AI Review Completed: Overall code structure is sound with minor optimization opportunities.",
            "risk_assessment": {
                "overall_risk_score": 15,
                "risk_level": "LOW",
                "key_risks": ["Minor complexity in helper logic"],
                "architectural_impact": "Low impact on overall module structure.",
                "testing_gaps": ["Consider adding unit tests for edge conditions."],
            },
            "comments": [
                {
                    "file_path": "src/main.py",
                    "line": 10,
                    "side": "RIGHT",
                    "title": "Optimization Opportunity",
                    "explanation": "Consider caching repeated lookup calls to reduce computation time.",
                    "suggestion": "# Add LRU cache decorator\n@lru_cache(maxsize=128)",
                    "priority": "LOW",
                    "category": "Performance",
                }
            ],
            "recommendations": [
                {
                    "topic": "Code Modularization",
                    "category": "Maintainability",
                    "action_item": "Keep function lengths under 50 lines for optimal readability.",
                    "code_example": None,
                    "priority": "LOW",
                }
            ],
        }

        raw_str = json.dumps(mock_json)
        prompt_tokens = len(system_prompt.split()) + len(user_prompt.split())
        completion_tokens = len(raw_str.split())

        return {
            "raw_text": raw_str,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model_id": target_model,
        }
