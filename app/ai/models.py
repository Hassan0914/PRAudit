"""Data models for AI-augmented code review outputs, risk assessments, and recommendations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AIPriority(str, Enum):
    """Priority level for AI review comments and recommendations."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RiskLevel(str, Enum):
    """Overall risk classification level."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class AIComment:
    """Represents an AI-generated inline code review comment."""

    file_path: str
    line: int
    side: str
    title: str
    explanation: str
    suggestion: Optional[str] = None
    priority: AIPriority = AIPriority.MEDIUM
    category: str = "General"


@dataclass
class AIRecommendation:
    """Represents an AI architectural or code quality recommendation."""

    topic: str
    category: str
    action_item: str
    code_example: Optional[str] = None
    priority: AIPriority = AIPriority.MEDIUM


@dataclass
class AIRiskAssessment:
    """Represents overall risk analysis computed by AI reasoning."""

    overall_risk_score: int  # 0 to 100
    risk_level: RiskLevel
    key_risks: List[str] = field(default_factory=list)
    architectural_impact: str = ""
    testing_gaps: List[str] = field(default_factory=list)


@dataclass
class AIReview:
    """Complete AI-augmented Pull Request review report."""

    review_id: str
    pr_id: str
    summary: str
    risk_assessment: AIRiskAssessment
    comments: List[AIComment] = field(default_factory=list)
    recommendations: List[AIRecommendation] = field(default_factory=list)
    total_tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    provider_name: str = "mock"
    model_name: str = "mock-model"
