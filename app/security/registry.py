"""Security Engine and Scanner Registry."""

from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging import setup_logger
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.security.models import (
    ScannerResult,
    SecurityFinding,
    SecurityReport,
    VulnerabilitySeverity,
)
from app.security.scanners.bandit_scanner import BanditScanner
from app.security.scanners.base import BaseSecurityScanner
from app.security.scanners.secret_scanner import SecretScanner

logger = setup_logger("security.registry")


class SecurityScannerRegistry:
    """Registry for security scanner plugins."""

    def __init__(self) -> None:
        """Initialize registry and register default scanners."""
        self._scanners: Dict[str, BaseSecurityScanner] = {}
        self.register(BanditScanner())
        self.register(SecretScanner())

    def register(self, scanner: BaseSecurityScanner) -> None:
        """Register a new security scanner plugin.

        Args:
            scanner: BaseSecurityScanner implementation.
        """
        self._scanners[scanner.name] = scanner
        logger.debug("Registered security scanner: %s", scanner.name)

    def get_scanners(self) -> List[BaseSecurityScanner]:
        """Return all registered security scanners."""
        return list(self._scanners.values())


class SecurityEngine:
    """Master engine running security scanners and generating aggregated security reports."""

    def __init__(self, registry: Optional[SecurityScannerRegistry] = None) -> None:
        """Initialize SecurityEngine."""
        self.registry = registry or SecurityScannerRegistry()

    def run_security_scan(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> SecurityReport:
        """Run all registered security scanners and build consolidated report.

        Args:
            repo_path: Target repository path.
            source_files: Discovered source files.
            parse_results: AST parse results.

        Returns:
            SecurityReport model.
        """
        logger.info("Executing security scanner plugins...")

        results: List[ScannerResult] = []
        all_findings: List[SecurityFinding] = []

        for scanner in self.registry.get_scanners():
            try:
                res = scanner.scan(repo_path, source_files, parse_results)
                results.append(res)
                all_findings.extend(res.findings)
            except Exception as exc:
                logger.error("Security scanner '%s' failed: %s", scanner.name, exc, exc_info=True)
                results.append(
                    ScannerResult(
                        scanner_name=scanner.name,
                        is_success=False,
                        execution_duration_ms=0.0,
                        error_message=str(exc),
                    )
                )

        crit_c = sum(1 for f in all_findings if f.severity == VulnerabilitySeverity.CRITICAL)
        high_c = sum(1 for f in all_findings if f.severity == VulnerabilitySeverity.HIGH)
        med_c = sum(1 for f in all_findings if f.severity == VulnerabilitySeverity.MEDIUM)
        low_c = sum(1 for f in all_findings if f.severity == VulnerabilitySeverity.LOW)

        logger.info(
            "Security scan completed: %d vulnerabilities (Critical: %d, High: %d, Med: %d)",
            len(all_findings),
            crit_c,
            high_c,
            med_c,
        )

        return SecurityReport(
            total_vulnerabilities=len(all_findings),
            critical_count=crit_c,
            high_count=high_c,
            medium_count=med_c,
            low_count=low_c,
            scanner_results=results,
            findings=all_findings,
        )
