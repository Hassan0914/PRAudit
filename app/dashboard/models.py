"""Data models for Web Dashboard statistics, analytics, and overview reports."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RepositoryOverview:
    """Overview statistics for a single repository."""

    repository_name: str
    total_files: int = 0
    total_lines: int = 0
    avg_maintainability: float = 0.0
    active_pr_reviews: int = 0


@dataclass
class TrendAnalytics:
    """Trend analytics tracking review activity over time."""

    period: str  # e.g., "7d", "30d"
    reviews_count: int = 0
    total_findings_count: int = 0
    avg_precision: float = 0.95
    avg_latency_ms: float = 120.0


@dataclass
class DeveloperActivity:
    """Activity summary for a developer."""

    developer_name: str
    prs_reviewed: int = 0
    feedback_provided: int = 0
    acceptance_rate: float = 0.90


@dataclass
class DashboardStatistics:
    """Aggregated dashboard statistics across organizations and repositories."""

    total_repositories: int = 0
    total_reviews_executed: int = 0
    total_findings_detected: int = 0
    overall_satisfaction_score: float = 95.0
    recent_repositories: List[RepositoryOverview] = field(default_factory=list)
    trend_analytics: List[TrendAnalytics] = field(default_factory=list)
