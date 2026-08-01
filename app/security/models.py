"""Data models for security findings, scanner results, and aggregated security reports."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class VulnerabilitySeverity(str, Enum):
    """Severity classification for security vulnerabilities."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConfidenceLevel(str, Enum):
    """Confidence level for security scanner findings."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class SecurityFinding:
    """Represents a single security vulnerability or secret finding."""

    finding_id: str
    vulnerability_id: str
    scanner_name: str
    file_path: str
    line: int
    severity: VulnerabilitySeverity
    confidence: ConfidenceLevel
    message: str
    cwe_id: Optional[str] = None
    recommendation: Optional[str] = None
    snippet: Optional[str] = None


@dataclass
class ScannerResult:
    """Result produced by a security scanner plugin."""

    scanner_name: str
    is_success: bool
    execution_duration_ms: float
    findings: List[SecurityFinding] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class SecurityReport:
    """Aggregated security report compiling findings across all scanners."""

    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scanner_results: List[ScannerResult] = field(default_factory=list)
    findings: List[SecurityFinding] = field(default_factory=list)
