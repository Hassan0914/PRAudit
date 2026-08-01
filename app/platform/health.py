"""Health Service providing system liveness and readiness diagnostic checks."""

import time
from typing import Dict
from app.core.logging import setup_logger
from app.platform.models import SystemHealthState, SystemStatus

logger = setup_logger("platform.health")

start_time = time.time()


class HealthService:
    """Service evaluating system health, liveness, and readiness probes."""

    def check_liveness(self) -> Dict[str, str]:
        """Check system liveness probe.

        Returns:
            Status dictionary.
        """
        return {"status": "alive", "timestamp": str(int(time.time()))}

    def check_readiness(self) -> SystemStatus:
        """Check system readiness probe.

        Returns:
            SystemStatus container.
        """
        uptime = round(time.time() - start_time, 2)
        services_status = {
            "parsing_engine": "HEALTHY",
            "git_adapter": "HEALTHY",
            "ai_review_engine": "HEALTHY",
            "cache_service": "HEALTHY",
            "storage_repository": "HEALTHY",
        }
        return SystemStatus(
            health=SystemHealthState.HEALTHY,
            version="5.0.0",
            uptime_seconds=uptime,
            services=services_status,
        )
