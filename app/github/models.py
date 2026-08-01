"""Data models for GitHub webhook events, review payloads, and integration states."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WebhookEvent:
    """Represents a validated incoming GitHub Webhook event."""

    event_type: str
    action: str
    repository_name: str
    pr_number: int
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubCommentPayload:
    """Represents an inline review comment formatted for GitHub API."""

    path: str
    line: int
    side: str
    body: str


@dataclass
class GitHubReviewPayload:
    """Represents a complete Pull Request review payload for GitHub API."""

    pr_number: int
    commit_id: str
    event: str  # APPROVE, REQUEST_CHANGES, COMMENT
    body: str
    comments: List[GitHubCommentPayload] = field(default_factory=list)
