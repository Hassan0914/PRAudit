"""Unit tests for Phase 26: Web Dashboard Backend."""

from app.dashboard.service import DashboardService


def test_dashboard_service() -> None:
    service = DashboardService()
    stats = service.get_dashboard_statistics()

    assert stats.total_repositories >= 1
    assert len(stats.recent_repositories) >= 1
    assert len(stats.trend_analytics) >= 1
