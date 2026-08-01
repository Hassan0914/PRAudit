"""Base abstract class for static analysis analyzer plugins."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.static_analysis.models import AnalyzerResult


class BaseAnalyzer(ABC):
    """Abstract base class for all static analysis plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of the analyzer plugin."""
        pass

    @abstractmethod
    def analyze(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> AnalyzerResult:
        """Run static analysis inspection over repository files.

        Args:
            repo_path: Absolute path to target repository.
            source_files: Discovered source files.
            parse_results: AST parse results.

        Returns:
            AnalyzerResult container.
        """
        pass
