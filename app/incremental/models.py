"""Data models for incremental delta analysis and dependency propagation."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChangedArtifact:
    """Represents a file artifact modified in a diff."""

    file_path: str
    change_type: str
    lines_added: int = 0
    lines_deleted: int = 0


@dataclass
class AffectedSymbol:
    """Represents a symbol directly or indirectly affected by changes."""

    symbol_id: str
    name: str
    file_path: str
    propagation_reason: str  # DIRECT, CALLER, DEPENDENCY


@dataclass
class AffectedChunk:
    """Represents a code chunk invalidated by diff line changes."""

    chunk_id: str
    file_path: str
    start_line: int
    end_line: int


@dataclass
class IncrementalDeltaReport:
    """Report detailing incremental delta analysis results."""

    pr_id: str
    changed_files_count: int
    affected_symbols: List[AffectedSymbol] = field(default_factory=list)
    affected_chunks: List[AffectedChunk] = field(default_factory=list)
    reanalyzed_files: List[str] = field(default_factory=list)
