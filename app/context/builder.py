"""Context Builder and Prompt Assembler implementing token budgeting."""

from typing import Dict, List, Optional
from app.context.models import AssembledContext, ContextSection
from app.context.providers import (
    DependencyContextProvider,
    DiffContextProvider,
    MetricsContextProvider,
    SecurityContextProvider,
    SymbolContextProvider,
)
from app.core.logging import setup_logger
from app.git.pr_models import PullRequest
from app.repository.intelligence import RepositoryIntelligenceResult
from app.review.impact_models import ImpactAnalysisReport

logger = setup_logger("context.builder")


class ContextBuilder:
    """Builder assembling targeted context for LLMs with token budgeting."""

    def __init__(self) -> None:
        self.symbol_provider = SymbolContextProvider()
        self.dep_provider = DependencyContextProvider()
        self.diff_provider = DiffContextProvider()
        self.metrics_provider = MetricsContextProvider()
        self.sec_provider = SecurityContextProvider()

    def assemble_context(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: ImpactAnalysisReport,
        token_budget: int = 16000,
    ) -> AssembledContext:
        """Assemble targeted prompt context respecting token_budget limit.

        Args:
            pr: PullRequest model.
            intelligence: RepositoryIntelligenceResult model.
            impact_report: ImpactAnalysisReport model.
            token_budget: Maximum allowed prompt token budget.

        Returns:
            AssembledContext object.
        """
        logger.info("Assembling context for PR %s (Token Budget: %d)", pr.pr_id, token_budget)

        raw_sections: List[ContextSection] = [
            self.diff_provider.get_section(pr),
            self.sec_provider.get_section(intelligence),
            self.symbol_provider.get_section(pr, intelligence),
            self.dep_provider.get_section(impact_report),
            self.metrics_provider.get_section(pr, intelligence),
        ]

        # Sort sections by priority (lowest integer = highest priority)
        sorted_sections = sorted(raw_sections, key=lambda s: s.priority)

        included_sections: List[ContextSection] = []
        total_tokens = 0
        is_truncated = False

        for section in sorted_sections:
            if total_tokens + section.estimated_tokens <= token_budget:
                included_sections.append(section)
                total_tokens += section.estimated_tokens
            else:
                is_truncated = True
                logger.warning("Token budget exceeded! Skipping section '%s'", section.title)

        assembled_lines: List[str] = []
        for sec in included_sections:
            assembled_lines.append(f"### {sec.title}\n{sec.content}\n")

        assembled_text = "\n".join(assembled_lines)

        return AssembledContext(
            pr_id=pr.pr_id,
            sections=included_sections,
            total_estimated_tokens=total_tokens,
            token_budget=token_budget,
            is_truncated=is_truncated,
            assembled_text=assembled_text,
        )
