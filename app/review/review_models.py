"""Data models for deterministic PR review findings, comments, and reports."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReviewFindingSeverity(str, Enum):
    """Severity classification for PR review findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ReviewVerdict(str, Enum):
    """Overall review verdict decision."""

    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


@dataclass
class ReviewFinding:
    """Represents a single deterministic review finding."""

    finding_id: str
    rule_id: str
    title: str
    description: str
    severity: ReviewFindingSeverity
    file_path: str
    line: int
    rule_category: str
    evidence: str
    recommendation: str


@dataclass
class ReviewComment:
    """Represents an inline review comment targeted to a specific PR line."""

    comment_id: str
    file_path: str
    line: int
    side: str
    body: str
    finding_id: Optional[str] = None


@dataclass
class ReviewSuggestion:
    """Represents a code suggestion block for a PR change."""

    file_path: str
    start_line: int
    end_line: int
    original_code: str
    suggested_code: str
    explanation: str


@dataclass
class ReviewSummary:
    """Aggregated summary of a Pull Request review."""

    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    verdict: ReviewVerdict = ReviewVerdict.APPROVE
    summary_text: str = ""


@dataclass
class ReviewReport:
    """Complete Pull Request review report."""

    review_id: str
    pr_id: str
    summary: ReviewSummary
    comments: List[ReviewComment] = field(default_factory=list)
    findings: List[ReviewFinding] = field(default_factory=list)
    suggestions: List[ReviewSuggestion] = field(default_factory=list)
