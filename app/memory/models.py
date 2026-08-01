"""Data models for review memory, historical trends, and developer feedback."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FeedbackType(str, Enum):
    """Types of developer feedback on review findings/suggestions."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    IGNORED = "IGNORED"


@dataclass
class HistoricalFinding:
    """Represents a historical finding recorded across PR reviews."""

    finding_id: str
    rule_id: str
    title: str
    file_path: str
    occurrence_count: int = 1
    first_seen_at: str = ""
    last_seen_at: str = ""


@dataclass
class HistoricalSuggestion:
    """Represents a historical code suggestion."""

    suggestion_id: str
    title: str
    file_path: str
    feedback: FeedbackType = FeedbackType.ACCEPTED
    developer_comment: Optional[str] = None


@dataclass
class DeveloperFeedback:
    """Record of developer interaction feedback on a review finding/suggestion."""

    feedback_id: str
    review_id: str
    finding_id: str
    feedback_type: FeedbackType
    developer_id: str
    comment: Optional[str] = None
    created_at: str = ""


@dataclass
class ReviewSnapshot:
    """Snapshot of a completed review stored in memory."""

    review_id: str
    pr_id: str
    repository_name: str
    verdict: str
    total_findings: int
    findings: List[HistoricalFinding] = field(default_factory=list)
    created_at: str = ""


@dataclass
class RepositoryKnowledge:
    """Accumulated knowledge base for a repository."""

    repository_name: str
    total_reviews_count: int = 0
    repeated_vulnerabilities_count: int = 0
    repeated_complexity_issues_count: int = 0
    top_problematic_files: List[str] = field(default_factory=list)


@dataclass
class ReviewHistory:
    """History container for a repository's past reviews and trends."""

    repository_name: str
    snapshots: List[ReviewSnapshot] = field(default_factory=list)
    feedback_logs: List[DeveloperFeedback] = field(default_factory=list)
    knowledge: RepositoryKnowledge = field(default_factory=lambda: RepositoryKnowledge("default"))
