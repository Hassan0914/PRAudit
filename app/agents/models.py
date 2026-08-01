"""Data models for multi-agent review findings and unified reports."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class AgentSeverity(str, Enum):
    """Severity levels for agent findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class AgentFinding:
    """Represents a finding produced by a specialized reviewer agent."""

    agent_name: str
    domain: str
    title: str
    description: str
    severity: AgentSeverity
    file_path: str
    line: int
    recommendation: str


@dataclass
class AgentResponse:
    """Container for a single specialized agent's response."""

    agent_name: str
    domain: str
    duration_ms: float
    findings: List[AgentFinding] = field(default_factory=list)
    confidence: float = 0.95


@dataclass
class UnifiedAIReviewReport:
    """Unified report aggregating specialized AI agent findings."""

    review_id: str
    pr_id: str
    agent_responses: List[AgentResponse] = field(default_factory=list)
    consolidated_findings: List[AgentFinding] = field(default_factory=list)
    overall_verdict: str = "APPROVE"
    total_tokens: int = 0
    total_cost_usd: float = 0.0
