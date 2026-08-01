"""Deterministic Review Engine evaluating PR changes without AI."""

import hashlib
import time
from typing import List, Optional

from app.core.logging import setup_logger
from app.git.pr_models import PullRequest
from app.repository.intelligence import RepositoryIntelligenceResult
from app.review.impact import ChangeImpactEngine
from app.review.impact_models import ImpactAnalysisReport
from app.review.review_models import (
    ReviewComment,
    ReviewFinding,
    ReviewFindingSeverity,
    ReviewReport,
    ReviewSummary,
    ReviewVerdict,
)
from app.review.rules.base import BaseReviewRule
from app.review.rules.rule_set import (
    HighComplexityRule,
    HighImpactRiskRule,
    LargeFunctionRule,
    SecurityVulnerabilityRule,
)

logger = setup_logger("review.engine")


class DeterministicReviewEngine:
    """Master engine generating rule-based PR review findings and comments."""

    def __init__(self, rules: Optional[List[BaseReviewRule]] = None) -> None:
        """Initialize DeterministicReviewEngine."""
        self.rules = rules or [
            HighComplexityRule(),
            LargeFunctionRule(),
            SecurityVulnerabilityRule(),
            HighImpactRiskRule(),
        ]
        self.impact_engine = ChangeImpactEngine()

    def review_pull_request(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: Optional[ImpactAnalysisReport] = None,
    ) -> ReviewReport:
        """Perform a complete deterministic PR review.

        Args:
            pr: PullRequest model.
            intelligence: RepositoryIntelligenceResult.
            impact_report: Optional pre-computed ImpactAnalysisReport.

        Returns:
            ReviewReport object.
        """
        review_id = hashlib.sha256(f"review:{pr.pr_id}:{time.time()}".encode()).hexdigest()[:16]
        logger.info("Executing deterministic review for PR %s (Review ID: %s)", pr.pr_id, review_id)

        if not impact_report:
            impact_report = self.impact_engine.analyze_impact(
                pr, intelligence.graphs, intelligence.symbol_index
            )

        all_findings: List[ReviewFinding] = []
        for rule in self.rules:
            try:
                findings = rule.evaluate(pr, intelligence, impact_report)
                all_findings.extend(findings)
            except Exception as exc:
                logger.error("Rule '%s' failed during PR evaluation: %s", rule.rule_id, exc)

        # Generate inline review comments from findings
        comments: List[ReviewComment] = []
        for f in all_findings:
            c_id = hashlib.sha256(f"comment:{f.finding_id}".encode()).hexdigest()[:16]
            body_text = f"**[{f.severity.value}] {f.title}**\n\n{f.description}\n\n*Recommendation*: {f.recommendation}"
            comments.append(
                ReviewComment(
                    comment_id=c_id,
                    file_path=f.file_path,
                    line=f.line,
                    side="RIGHT",
                    body=body_text,
                    finding_id=f.finding_id,
                )
            )

        # Calculate severity counts and verdict
        crit_c = sum(1 for f in all_findings if f.severity == ReviewFindingSeverity.CRITICAL)
        high_c = sum(1 for f in all_findings if f.severity == ReviewFindingSeverity.HIGH)
        med_c = sum(1 for f in all_findings if f.severity == ReviewFindingSeverity.MEDIUM)
        low_c = sum(1 for f in all_findings if f.severity == ReviewFindingSeverity.LOW)

        verdict = ReviewVerdict.APPROVE
        if crit_c > 0 or high_c > 0:
            verdict = ReviewVerdict.REQUEST_CHANGES
        elif med_c > 0:
            verdict = ReviewVerdict.COMMENT

        summary_text = (
            f"PRAudit Review Completed: {len(all_findings)} finding(s) detected. "
            f"Verdict: {verdict.value} (Critical: {crit_c}, High: {high_c}, Medium: {med_c}, Low: {low_c})."
        )

        summary = ReviewSummary(
            total_findings=len(all_findings),
            critical_count=crit_c,
            high_count=high_c,
            medium_count=med_c,
            low_count=low_c,
            verdict=verdict,
            summary_text=summary_text,
        )

        logger.info(
            "Review generated for PR %s: Verdict=%s, Findings=%d",
            pr.pr_id,
            verdict.value,
            len(all_findings),
        )

        return ReviewReport(
            review_id=review_id,
            pr_id=pr.pr_id,
            summary=summary,
            comments=comments,
            findings=all_findings,
            suggestions=[],
        )
