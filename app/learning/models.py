"""Data models for developer feedback learning metrics and accuracy scores."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FeedbackEvent:
    """Represents a single developer feedback event."""

    event_id: str
    rule_id: str
    agent_name: str
    feedback_action: str  # ACCEPTED, REJECTED, IGNORED
    is_false_positive: bool = False
    comment: Optional[str] = None
    created_at: str = ""


@dataclass
class RuleAccuracy:
    """Accuracy metrics for a specific review rule."""

    rule_id: str
    total_evaluations: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    acceptance_rate: float = 1.0


@dataclass
class AgentAccuracy:
    """Accuracy metrics for a specialized reviewer agent."""

    agent_name: str
    total_findings: int = 0
    accepted_findings: int = 0
    acceptance_rate: float = 1.0


@dataclass
class LearningMetrics:
    """Aggregate accuracy and developer satisfaction metrics."""

    total_feedback_events: int = 0
    precision: float = 1.0
    recall: float = 1.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    acceptance_rate: float = 1.0
    developer_satisfaction_score: float = 100.0  # 0 to 100
    rule_accuracies: List[RuleAccuracy] = field(default_factory=list)
    agent_accuracies: List[AgentAccuracy] = field(default_factory=list)
