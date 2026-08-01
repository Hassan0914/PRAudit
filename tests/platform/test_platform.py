"""Unit tests for Phase 30: Production Platform and Health Services."""

from app.platform.health import HealthService
from app.platform.manager import ConfigurationManager, MonitoringService


def test_platform_health_service() -> None:
    service = HealthService()
    liveness = service.check_liveness()
    assert liveness["status"] == "alive"

    readiness = service.check_readiness()
    assert readiness.health.value == "HEALTHY"
    assert readiness.version == "5.0.0"


def test_configuration_manager_and_monitoring() -> None:
    config_mgr = ConfigurationManager()
    cfg = config_mgr.get_config()
    assert cfg.environment == "production"

    mon_service = MonitoringService()
    mon_service.record_metric("review_latency", 120.5, {"repo": "PRAudit"})
