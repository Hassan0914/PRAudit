"""Telemetry Tracker monitoring token usage, API costs in USD, and execution latency."""

from dataclasses import dataclass, field
from typing import Dict, List
from app.core.logging import setup_logger

logger = setup_logger("telemetry.tracker")


@dataclass
class TelemetryEntry:
    """Represents a single telemetry event log."""

    event_name: str
    tokens_used: int
    cost_usd: float
    latency_ms: float


class TelemetryTracker:
    """Tracker accumulating token usage, cumulative costs, and review performance metrics."""

    def __init__(self) -> None:
        self.entries: List[TelemetryEntry] = []

    def record_event(self, event_name: str, tokens_used: int, cost_usd: float, latency_ms: float) -> None:
        """Record a telemetry event."""
        entry = TelemetryEntry(
            event_name=event_name,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )
        self.entries.append(entry)
        logger.debug("Telemetry recorded: %s (Tokens: %d, Cost: $%.6f, Latency: %.2fms)", event_name, tokens_used, cost_usd, latency_ms)

    def get_summary(self) -> Dict[str, float]:
        """Get aggregate telemetry metrics summary."""
        tot_tokens = sum(e.tokens_used for e in self.entries)
        tot_cost = sum(e.cost_usd for e in self.entries)
        avg_latency = (
            sum(e.latency_ms for e in self.entries) / len(self.entries) if self.entries else 0.0
        )

        return {
            "total_events": len(self.entries),
            "total_tokens_used": tot_tokens,
            "total_cost_usd": round(tot_cost, 6),
            "average_latency_ms": round(avg_latency, 2),
        }
