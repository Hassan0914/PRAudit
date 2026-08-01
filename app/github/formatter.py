"""Markdown formatter converting PRAudit review reports into GitHub PR comments."""

from typing import List
from app.github.models import GitHubCommentPayload, GitHubReviewPayload
from app.review.review_models import ReviewReport

class GitHubCommentFormatter:
    """Formatter providing clean Markdown formatting for GitHub review submissions."""

    def format_review(self, report: ReviewReport, pr_number: int, commit_id: str) -> GitHubReviewPayload:
        """Format a PRAudit ReviewReport into a GitHubReviewPayload.

        Args:
            report: ReviewReport instance.
            pr_number: GitHub PR number.
            commit_id: Head commit SHA.

        Returns:
            GitHubReviewPayload object.
        """
        summary_md = self.format_summary_markdown(report)
        comments = [
            GitHubCommentPayload(
                path=c.file_path,
                line=c.line,
                side=c.side,
                body=c.body,
            )
            for c in report.comments
        ]

        gh_event = report.summary.verdict.value

        return GitHubReviewPayload(
            pr_number=pr_number,
            commit_id=commit_id,
            event=gh_event,
            body=summary_md,
            comments=comments,
        )

    def format_summary_markdown(self, report: ReviewReport) -> str:
        """Format ReviewSummary into clean GitHub Markdown summary table."""
        s = report.summary
        lines = [
            f"## 🔍 PRAudit Automated Code Review",
            f"",
            f"**Verdict**: `{s.verdict.value}`",
            f"**Total Findings**: `{s.total_findings}`",
            f"",
            f"| Severity | Count |",
            f"| :--- | :--- |",
            f"| 🚨 Critical | `{s.critical_count}` |",
            f"| 🔴 High | `{s.high_count}` |",
            f"| 🟡 Medium | `{s.medium_count}` |",
            f"| 🟢 Low | `{s.low_count}` |",
            f"",
            f"---",
            f"*Generated deterministically by PRAudit Repository Intelligence Engine.*",
        ]
        return "\n".join(lines)
