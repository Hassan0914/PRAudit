"""Deterministic rule implementations for PR code quality and security reviews."""

import hashlib
from typing import List

from app.core.logging import setup_logger
from app.git.pr_models import PullRequest
from app.repository.intelligence import RepositoryIntelligenceResult
from app.review.impact_models import ImpactAnalysisReport
from app.review.review_models import ReviewFinding, ReviewFindingSeverity
from app.review.rules.base import BaseReviewRule

logger = setup_logger("review.rules")


class HighComplexityRule(BaseReviewRule):
    """Rule flagging modified/added functions exceeding cyclomatic complexity threshold (default > 10)."""

    def __init__(self, threshold: int = 10) -> None:
        self.threshold = threshold

    @property
    def rule_id(self) -> str:
        return "PR-COMPLEXITY-001"

    @property
    def category(self) -> str:
        return "Complexity"

    def evaluate(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: ImpactAnalysisReport,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []

        for pr_file in pr.files:
            fm = intelligence.metrics.file_metrics.get(pr_file.file_path)
            if not fm:
                continue

            for func in fm.functions:
                if func.cyclomatic_complexity > self.threshold:
                    # Check if line overlap exists in PR
                    for hunk in pr_file.hunks:
                        for lc in hunk.line_changes:
                            if func.start_line <= lc.line_number <= func.end_line:
                                f_id = hashlib.sha256(
                                    f"rule_comp:{pr_file.file_path}:{func.start_line}".encode()
                                ).hexdigest()[:16]

                                findings.append(
                                    ReviewFinding(
                                        finding_id=f_id,
                                        rule_id=self.rule_id,
                                        title=f"High Cyclomatic Complexity in '{func.name}'",
                                        description=f"Function '{func.name}' has a Cyclomatic Complexity of {func.cyclomatic_complexity}, exceeding the maximum allowed threshold of {self.threshold}.",
                                        severity=ReviewFindingSeverity.HIGH,
                                        file_path=pr_file.file_path,
                                        line=func.start_line,
                                        rule_category=self.category,
                                        evidence=f"Complexity: {func.cyclomatic_complexity} (Threshold: {self.threshold})",
                                        recommendation="Refactor function into smaller single-responsibility helper functions.",
                                    )
                                )
                                break
                        else:
                            continue
                        break

        return findings


class LargeFunctionRule(BaseReviewRule):
    """Rule flagging functions exceeding maximum line count (default > 50 lines)."""

    def __init__(self, max_lines: int = 50) -> None:
        self.max_lines = max_lines

    @property
    def rule_id(self) -> str:
        return "PR-SIZE-001"

    @property
    def category(self) -> str:
        return "Maintainability"

    def evaluate(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: ImpactAnalysisReport,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []

        for pr_file in pr.files:
            fm = intelligence.metrics.file_metrics.get(pr_file.file_path)
            if not fm:
                continue

            for func in fm.functions:
                if func.lines_of_code > self.max_lines:
                    f_id = hashlib.sha256(
                        f"rule_size:{pr_file.file_path}:{func.start_line}".encode()
                    ).hexdigest()[:16]

                    findings.append(
                        ReviewFinding(
                            finding_id=f_id,
                            rule_id=self.rule_id,
                            title=f"Large Function Length in '{func.name}'",
                            description=f"Function '{func.name}' spans {func.lines_of_code} lines of code, exceeding the limit of {self.max_lines} lines.",
                            severity=ReviewFindingSeverity.MEDIUM,
                            file_path=pr_file.file_path,
                            line=func.start_line,
                            rule_category=self.category,
                            evidence=f"Lines of code: {func.lines_of_code} (Limit: {self.max_lines})",
                            recommendation="Decompose large function into modular sub-routines.",
                        )
                    )

        return findings


class SecurityVulnerabilityRule(BaseReviewRule):
    """Rule mapping security vulnerabilities (eval, exec, hardcoded secrets) to PR diff lines."""

    @property
    def rule_id(self) -> str:
        return "PR-SECURITY-001"

    @property
    def category(self) -> str:
        return "Security"

    def evaluate(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: ImpactAnalysisReport,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        sec_findings = intelligence.security.findings

        for pr_file in pr.files:
            for hunk in pr_file.hunks:
                for lc in hunk.line_changes:
                    for sec in sec_findings:
                        if sec.file_path == pr_file.file_path and sec.line == lc.line_number:
                            sev = (
                                ReviewFindingSeverity.CRITICAL
                                if sec.severity.value == "CRITICAL"
                                else ReviewFindingSeverity.HIGH
                            )
                            f_id = hashlib.sha256(
                                f"pr_sec:{sec.finding_id}:{lc.line_number}".encode()
                            ).hexdigest()[:16]

                            findings.append(
                                ReviewFinding(
                                    finding_id=f_id,
                                    rule_id=sec.vulnerability_id,
                                    title=f"Security Vulnerability: {sec.message}",
                                    description=sec.message,
                                    severity=sev,
                                    file_path=pr_file.file_path,
                                    line=lc.line_number,
                                    rule_category=self.category,
                                    evidence=f"CWE: {sec.cwe_id or 'N/A'} | Snippet: {sec.snippet or 'N/A'}",
                                    recommendation=sec.recommendation or "Fix security issue before merging.",
                                )
                            )

        return findings


class HighImpactRiskRule(BaseReviewRule):
    """Rule flagging PR changes with high downstream call impact (> 5 affected callers)."""

    def __init__(self, impact_threshold: int = 5) -> None:
        self.impact_threshold = impact_threshold

    @property
    def rule_id(self) -> str:
        return "PR-IMPACT-001"

    @property
    def category(self) -> str:
        return "Architecture"

    def evaluate(
        self,
        pr: PullRequest,
        intelligence: RepositoryIntelligenceResult,
        impact_report: ImpactAnalysisReport,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []

        if impact_report.statistics.downstream_callers_count > self.impact_threshold:
            for pr_file in pr.files:
                f_id = hashlib.sha256(f"pr_impact:{pr_file.file_path}".encode()).hexdigest()[:16]
                findings.append(
                    ReviewFinding(
                        finding_id=f_id,
                        rule_id=self.rule_id,
                        title="High Change Impact Radius",
                        description=f"Changes in '{pr_file.file_path}' impact {impact_report.statistics.downstream_callers_count} downstream callers across {len(impact_report.impacted_files)} files.",
                        severity=ReviewFindingSeverity.HIGH,
                        file_path=pr_file.file_path,
                        line=1,
                        rule_category=self.category,
                        evidence=f"Downstream callers: {impact_report.statistics.downstream_callers_count}",
                        recommendation="Run comprehensive regression tests for downstream callers.",
                    )
                )

        return findings
