"""Core exception classes for the PRAudit platform.

All custom exceptions derive from PRAuditError to allow unified error handling.
"""

from typing import Any, Dict, Optional


class PRAuditError(Exception):
    """Base exception for all errors raised within the PRAudit platform."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PRAuditError.

        Args:
            message: Explanation of the error.
            details: Optional dictionary containing context or metadata.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return formatted string representation of the exception."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class RepositoryNotFoundError(PRAuditError):
    """Raised when a target repository path does not exist."""

    pass


class InvalidRepositoryError(PRAuditError):
    """Raised when a path is not a valid directory or repository."""

    pass


class ParserNotFoundError(PRAuditError):
    """Raised when a tree-sitter parser is not available for a given language."""

    pass


class ASTParsingError(PRAuditError):
    """Raised when syntax parsing encounters an unrecoverable failure."""

    pass


class ChunkExtractionError(PRAuditError):
    """Raised when semantic chunk extraction fails."""

    pass


class SymbolExtractionError(PRAuditError):
    """Raised when symbol extraction fails."""

    pass
