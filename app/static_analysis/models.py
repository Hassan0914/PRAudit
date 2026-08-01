"""Data models for static analysis findings, analyzer results, and aggregated reports."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FindingSeverity(str, Enum):
    """Severity levels for static analysis and code quality findings."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class StaticAnalysisFinding:
    """Represents a single static analysis rule finding or issue."""

    finding_id: str
    rule_id: str
    analyzer_name: str
    file_path: str
    line: int
    column: int
    severity: FindingSeverity
    message: str
    snippet: Optional[str] = None


@dataclass
class AnalyzerResult:
    """Result container produced by an individual static analysis plugin."""

    analyzer_name: str
    is_success: bool
    execution_duration_ms: float
    findings: List[StaticAnalysisFinding] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class StaticAnalysisReport:
    """Aggregated static analysis report compiling findings across all plugins."""

    total_findings: int = 0
    high_severity_count: int = 0
    medium_severity_count: int = 0
    low_severity_count: int = 0
    info_severity_count: int = 0
    analyzer_results: List[AnalyzerResult] = field(default_factory=list)
    findings: List[StaticAnalysisFinding] = field(default_factory=list)
