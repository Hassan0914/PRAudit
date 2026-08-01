"""Base abstract class for security scanner plugins."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.security.models import ScannerResult


class BaseSecurityScanner(ABC):
    """Abstract base class for all security scanners."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the security scanner."""
        pass

    @abstractmethod
    def scan(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> ScannerResult:
        """Run security scan over repository files.

        Args:
            repo_path: Absolute path to target repository.
            source_files: Discovered source files.
            parse_results: AST parse results.

        Returns:
            ScannerResult model.
        """
        pass
