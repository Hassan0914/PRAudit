"""Data models for AI evaluation, benchmark metrics, precision, and recall."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EvaluationMetric:
    """Represents a single evaluation benchmark metric."""

    name: str
    value: float
    target_benchmark: float
    status: str  # PASSED, WARNING, FAILED


@dataclass
class EvaluationReport:
    """Container for AI review evaluation metrics and precision/recall scores."""

    review_id: str
    precision: float            # True Positives / (True Positives + False Positives)
    recall: float               # True Positives / (True Positives + False Negatives)
    false_positives_count: int
    false_negatives_count: int
    latency_ms: float
    token_efficiency_score: float  # 0.0 to 100.0
    metrics: List[EvaluationMetric] = field(default_factory=list)
