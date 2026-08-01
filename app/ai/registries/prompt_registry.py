"""Prompt registry storing versioned system prompts and template schemas."""

from dataclasses import dataclass
from typing import Dict, Optional
from app.core.logging import setup_logger

logger = setup_logger("ai.prompt_registry")


@dataclass
class PromptVersion:
    """Represents a versioned prompt specification."""

    version: str
    name: str
    system_prompt: str
    user_template: str


class PromptRegistry:
    """Registry maintaining versioned prompt templates."""

    def __init__(self) -> None:
        """Initialize PromptRegistry with default versioned templates."""
        self._prompts: Dict[str, PromptVersion] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default version 1.0.0 review prompt."""
        v1 = PromptVersion(
            version="1.0.0",
            name="default-pr-review",
            system_prompt=(
                "You are an expert Staff Software Engineer and Security Specialist reviewing Pull Requests. "
                "Analyze the provided PR diff, deterministic findings, impact graphs, and code metrics. "
                "Output your review strictly as a valid JSON object matching the required schema."
            ),
            user_template=(
                "Target PR ID: {pr_id}\n\n"
                "== Context & Deterministic Intelligence ==\n"
                "{context_text}\n\n"
                "== Pull Request Diff ==\n"
                "{diff_text}\n\n"
                "Provide structured review comments, recommendations, and risk assessment."
            ),
        )
        self.register_prompt(v1)

    def register_prompt(self, prompt: PromptVersion) -> None:
        """Register a versioned prompt."""
        key = f"{prompt.name}:{prompt.version}"
        self._prompts[key] = prompt
        logger.info("Registered prompt '%s' (version %s)", prompt.name, prompt.version)

    def get_prompt(self, name: str = "default-pr-review", version: str = "1.0.0") -> PromptVersion:
        """Retrieve a versioned prompt template."""
        key = f"{name}:{version}"
        if key not in self._prompts:
            logger.warning("Prompt '%s' not found. Falling back to default-pr-review:1.0.0", key)
            return self._prompts["default-pr-review:1.0.0"]
        return self._prompts[key]

    def render_user_prompt(
        self, name: str, version: str, pr_id: str, context_text: str, diff_text: str
    ) -> str:
        """Render user prompt template with variable substitution."""
        pv = self.get_prompt(name, version)
        return pv.user_template.format(
            pr_id=pr_id, context_text=context_text, diff_text=diff_text
        )
