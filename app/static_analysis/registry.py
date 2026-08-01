"""Static Analysis Engine and Analyzer Registry."""

from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging import setup_logger
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.static_analysis.analyzers.base import BaseAnalyzer
from app.static_analysis.analyzers.javascript_eslint import ESLintAnalyzer
from app.static_analysis.analyzers.python_mypy import MyPyAnalyzer
from app.static_analysis.analyzers.python_ruff import RuffAnalyzer
from app.static_analysis.models import (
    AnalyzerResult,
    FindingSeverity,
    StaticAnalysisFinding,
    StaticAnalysisReport,
)

logger = setup_logger("static_analysis.registry")


class AnalyzerRegistry:
    """Registry managing static analysis analyzer plugins."""

    def __init__(self) -> None:
        """Initialize registry and register default analyzers."""
        self._analyzers: Dict[str, BaseAnalyzer] = {}
        self.register(RuffAnalyzer())
        self.register(MyPyAnalyzer())
        self.register(ESLintAnalyzer())

    def register(self, analyzer: BaseAnalyzer) -> None:
        """Register a new static analysis plugin.

        Args:
            analyzer: BaseAnalyzer implementation.
        """
        self._analyzers[analyzer.name] = analyzer
        logger.debug("Registered static analyzer: %s", analyzer.name)

    def get_analyzers(self) -> List[BaseAnalyzer]:
        """Return all registered analyzer plugins."""
        return list(self._analyzers.values())


class StaticAnalysisEngine:
    """Engine executing static analysis plugins and generating aggregated reports."""

    def __init__(self, registry: Optional[AnalyzerRegistry] = None) -> None:
        """Initialize StaticAnalysisEngine."""
        self.registry = registry or AnalyzerRegistry()

    def run_analysis(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> StaticAnalysisReport:
        """Run all registered static analyzers and build consolidated report.

        Args:
            repo_path: Target repository root path.
            source_files: Discovered source files.
            parse_results: AST parse results.

        Returns:
            StaticAnalysisReport model.
        """
        logger.info("Executing static analysis plugins...")

        results: List[AnalyzerResult] = []
        all_findings: List[StaticAnalysisFinding] = []

        for analyzer in self.registry.get_analyzers():
            try:
                res = analyzer.analyze(repo_path, source_files, parse_results)
                results.append(res)
                all_findings.extend(res.findings)
            except Exception as exc:
                logger.error("Analyzer '%s' failed during execution: %s", analyzer.name, exc, exc_info=True)
                results.append(
                    AnalyzerResult(
                        analyzer_name=analyzer.name,
                        is_success=False,
                        execution_duration_ms=0.0,
                        error_message=str(exc),
                    )
                )

        high_c = sum(1 for f in all_findings if f.severity == FindingSeverity.HIGH)
        med_c = sum(1 for f in all_findings if f.severity == FindingSeverity.MEDIUM)
        low_c = sum(1 for f in all_findings if f.severity == FindingSeverity.LOW)
        info_c = sum(1 for f in all_findings if f.severity == FindingSeverity.INFO)

        logger.info(
            "Static analysis completed: %d total findings (High: %d, Med: %d, Low: %d)",
            len(all_findings),
            high_c,
            med_c,
            low_c,
        )

        return StaticAnalysisReport(
            total_findings=len(all_findings),
            high_severity_count=high_c,
            medium_severity_count=med_c,
            low_severity_count=low_c,
            info_severity_count=info_c,
            analyzer_results=results,
            findings=all_findings,
        )
