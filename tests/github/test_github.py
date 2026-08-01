"""Unit tests for Phase 15: GitHub Integration."""

from app.github.auth import GitHubAuthenticationService
from app.github.formatter import GitHubCommentFormatter
from app.github.publisher import GitHubReviewPublisher
from app.github.webhooks import GitHubWebhookService
from app.review.review_models import ReviewReport, ReviewSummary, ReviewVerdict


def test_github_webhook_parsing() -> None:
    """Test parsing incoming webhook JSON payload."""
    service = GitHubWebhookService(secret="test_secret")

    payload = {
        "action": "synchronize",
        "number": 42,
        "repository": {"name": "PRAudit"},
        "pull_request": {"number": 42},
    }

    event = service.parse_event("pull_request", payload)
    assert event.event_type == "pull_request"
    assert event.action == "synchronize"
    assert event.repository_name == "PRAudit"
    assert event.pr_number == 42


def test_github_comment_formatting() -> None:
    """Test formatting review report into GitHub Markdown."""
    formatter = GitHubCommentFormatter()
    report = ReviewReport(
        review_id="rev_100",
        pr_id="PR-42",
        summary=ReviewSummary(total_findings=2, critical_count=0, high_count=1, verdict=ReviewVerdict.REQUEST_CHANGES),
        comments=[],
        findings=[],
        suggestions=[],
    )

    gh_payload = formatter.format_review(report, pr_number=42, commit_id="sha123")
    assert gh_payload.event == "REQUEST_CHANGES"
    assert "PRAudit Automated Code Review" in gh_payload.body


def test_github_review_publisher() -> None:
    """Test publishing review to GitHub API publisher."""
    publisher = GitHubReviewPublisher()
    report = ReviewReport(
        review_id="rev_101",
        pr_id="PR-99",
        summary=ReviewSummary(total_findings=0, verdict=ReviewVerdict.APPROVE),
        comments=[],
        findings=[],
    )

    res = publisher.publish_review("org", "repo", pr_number=99, commit_id="sha99", report=report)
    assert res["status"] == "published"
    assert res["verdict"] == "APPROVE"
