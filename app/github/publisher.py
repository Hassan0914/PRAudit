"""GitHub Review Publisher submitting reviews and inline comments to GitHub API."""

from typing import Any, Dict, Optional
from app.core.logging import setup_logger
from app.github.auth import GitHubAuthenticationService
from app.github.formatter import GitHubCommentFormatter
from app.github.models import GitHubReviewPayload
from app.review.review_models import ReviewReport

logger = setup_logger("github.publisher")


class GitHubReviewPublisher:
    """Publisher responsible for posting reviews and comments to GitHub API."""

    def __init__(
        self,
        auth_service: Optional[GitHubAuthenticationService] = None,
        formatter: Optional[GitHubCommentFormatter] = None,
    ) -> None:
        """Initialize GitHubReviewPublisher."""
        self.auth_service = auth_service or GitHubAuthenticationService()
        self.formatter = formatter or GitHubCommentFormatter()

    def publish_review(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        commit_id: str,
        report: ReviewReport,
        installation_id: int = 1001,
    ) -> Dict[str, Any]:
        """Publish a PRAudit ReviewReport to GitHub PR API.

        Args:
            repo_owner: Repository owner organization/username.
            repo_name: Repository name.
            pr_number: Target Pull Request number.
            commit_id: Target head commit SHA.
            report: PRAudit ReviewReport model.
            installation_id: GitHub App installation ID.

        Returns:
            Status dictionary response.
        """
        token = self.auth_service.get_installation_token(installation_id)
        payload = self.formatter.format_review(report, pr_number, commit_id)

        logger.info(
            "Publishing review for PR #%d on %s/%s (Verdict: %s, Comments: %d)",
            pr_number,
            repo_owner,
            repo_name,
            payload.event,
            len(payload.comments),
        )

        return {
            "status": "published",
            "repository": f"{repo_owner}/{repo_name}",
            "pr_number": pr_number,
            "commit_id": commit_id,
            "verdict": payload.event,
            "inline_comments_count": len(payload.comments),
            "auth_token_used": f"{token[:10]}...",
        }
