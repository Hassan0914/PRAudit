"""Data models for system deployment configurations, health checks, and readiness."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SystemHealthState(str, Enum):
    """System health status states."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class DeploymentConfiguration:
    """Deployment configuration parameters."""

    environment: str = "production"
    max_workers: int = 4
    rate_limit_per_minute: int = 60
    enable_opentelemetry: bool = True
    log_level: str = "INFO"


@dataclass
class SystemStatus:
    """Overall system readiness and liveness status."""

    health: SystemHealthState
    version: str = "5.0.0"
    uptime_seconds: float = 0.0
    services: Dict[str, str] = field(default_factory=dict)
