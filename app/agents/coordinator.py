"""Review Coordinator launching specialized agents and aggregating unified review reports."""

import hashlib
import time
from typing import List, Optional

from app.agents.base_agent import BaseReviewAgent
from app.agents.models import AgentFinding, AgentResponse, AgentSeverity, UnifiedAIReviewReport
from app.agents.specialized_agents import (
    ArchitectureReviewer,
    DocumentationReviewer,
    MaintainabilityReviewer,
    PerformanceReviewer,
    SecurityReviewer,
    TestingReviewer,
)
from app.core.logging import setup_logger

logger = setup_logger("agents.coordinator")


class ReviewCoordinator:
    """Coordinator orchestrating multi-agent code reviews."""

    def __init__(self, agents: Optional[List[BaseReviewAgent]] = None) -> None:
        """Initialize ReviewCoordinator with default specialized agents."""
        self.agents = agents or [
            ArchitectureReviewer(),
            SecurityReviewer(),
            PerformanceReviewer(),
            MaintainabilityReviewer(),
            TestingReviewer(),
            DocumentationReviewer(),
        ]

    def coordinate_review(self, pr_id: str, context_text: str, diff_text: str) -> UnifiedAIReviewReport:
        """Launch specialized agents, aggregate findings, deduplicate, and rank severity.

        Args:
            pr_id: Pull Request ID.
            context_text: Assembled prompt context text.
            diff_text: Pull Request diff text.

        Returns:
            UnifiedAIReviewReport object.
        """
        review_id = hashlib.sha256(f"unified:{pr_id}:{time.time()}".encode()).hexdigest()[:16]
        logger.info("Coordinating multi-agent review for PR %s (Agents: %d)", pr_id, len(self.agents))

        responses: List[AgentResponse] = []
        all_findings: List[AgentFinding] = []

        for agent in self.agents:
            try:
                res = agent.review(pr_id, context_text, diff_text)
                responses.append(res)
                all_findings.extend(res.findings)
            except Exception as exc:
                logger.error("Agent '%s' execution failed: %s", agent.agent_name, exc)

        # De-duplicate findings by title and file_path
        unique_findings: List[AgentFinding] = []
        seen_keys = set()
        for f in all_findings:
            key = f"{f.title}:{f.file_path}:{f.line}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_findings.append(f)

        # Rank severity (CRITICAL > HIGH > MEDIUM > LOW > INFO)
        sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        unique_findings.sort(key=lambda f: sev_rank.get(f.severity.value, 5))

        # Determine overall verdict
        has_critical_or_high = any(
            f.severity in {AgentSeverity.CRITICAL, AgentSeverity.HIGH} for f in unique_findings
        )
        verdict = "REQUEST_CHANGES" if has_critical_or_high else "APPROVE"

        logger.info("Multi-agent review complete for PR %s: Verdict=%s, Total Findings=%d", pr_id, verdict, len(unique_findings))

        return UnifiedAIReviewReport(
            review_id=review_id,
            pr_id=pr_id,
            agent_responses=responses,
            consolidated_findings=unique_findings,
            overall_verdict=verdict,
            total_tokens=1200,
            total_cost_usd=0.0036,
        )
