"""Base abstract reviewer agent class."""

from abc import ABC, abstractmethod
from typing import Optional
from app.agents.models import AgentResponse
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockLLMProvider


class BaseReviewAgent(ABC):
    """Abstract base class for domain-specialized reviewer agents."""

    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        self.provider = provider or MockLLMProvider()

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Name of the specialized agent."""
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain area (Architecture, Security, Performance, etc.)."""
        pass

    @abstractmethod
    def review(self, pr_id: str, context_text: str, diff_text: str) -> AgentResponse:
        """Execute domain-specific code review.

        Args:
            pr_id: Target PR ID string.
            context_text: Assembled context text.
            diff_text: Pull Request diff text.

        Returns:
            AgentResponse object.
        """
        pass
