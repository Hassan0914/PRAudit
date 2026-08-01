"""Base abstract class for deterministic review rules."""

from abc import ABC, abstractmethod
from typing import List

from app.git.pr_models import PullRequest
from app.repository.intelligence import RepositoryIntelligenceResult
from app.review.impact_models import ImpactAnalysisReport
from app.review.review_models import ReviewFinding


class BaseReviewRule(ABC):
    """Abstract base class for all deterministic PR review rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier string of the rule."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Rule category (Complexity, Security, Architecture, Style, Impact)."""
        pass

    @abstractmethod
    def evaluate(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: ImpactAnalysisReport,
    ) -> List[ReviewFinding]:
        """Evaluate deterministic rule logic over PR diff and repository intelligence.

        Args:
            pr: PullRequest model.
            intelligence: RepositoryIntelligenceResult model.
            impact_report: ImpactAnalysisReport model.

        Returns:
            List of ReviewFinding objects.
        """
        pass
