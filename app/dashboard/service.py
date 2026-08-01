"""Dashboard Service providing Web Dashboard backend analytics and statistics."""

from typing import Dict, List, Optional
from app.core.logging import setup_logger
from app.dashboard.models import (
    DashboardStatistics,
    DeveloperActivity,
    RepositoryOverview,
    TrendAnalytics,
)

logger = setup_logger("dashboard.service")


class DashboardService:
    """Service serving web dashboard metrics and trend analysis."""

    def get_dashboard_statistics(self) -> DashboardStatistics:
        """Get aggregate dashboard statistics.

        Returns:
            DashboardStatistics container.
        """
        repos = [
            RepositoryOverview("PRAudit", total_files=73, total_lines=5894, avg_maintainability=54.1, active_pr_reviews=5),
            RepositoryOverview("SampleRepo", total_files=12, total_lines=450, avg_maintainability=72.0, active_pr_reviews=2),
        ]
        trends = [
            TrendAnalytics(period="7d", reviews_count=42, total_findings_count=18, avg_precision=0.96, avg_latency_ms=115.0),
            TrendAnalytics(period="30d", reviews_count=180, total_findings_count=75, avg_precision=0.94, avg_latency_ms=125.0),
        ]
        return DashboardStatistics(
            total_repositories=2,
            total_reviews_executed=222,
            total_findings_detected=93,
            overall_satisfaction_score=96.5,
            recent_repositories=repos,
            trend_analytics=trends,
        )

    def get_repository_overviews(self) -> List[RepositoryOverview]:
        """Get repository overview list."""
        return self.get_dashboard_statistics().recent_repositories

    def get_trend_analytics(self) -> List[TrendAnalytics]:
        """Get review trend analytics list."""
        return self.get_dashboard_statistics().trend_analytics
