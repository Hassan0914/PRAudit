"""Repository models representing source files, repository metadata, and statistics."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from app.core.types import Language


@dataclass
class SourceFile:
    """Represents a discovered source file within a repository."""

    relative_path: str
    absolute_path: Path
    extension: str
    language: Language
    size_bytes: int
    line_count: int
    is_supported: bool = True
    content_hash: Optional[str] = None


@dataclass
class RepositoryMetadata:
    """Metadata describing a target code repository."""

    root_path: Path
    name: str
    is_git_repository: bool
    git_head_commit: Optional[str] = None
    discovered_at_utc: Optional[str] = None


@dataclass
class LanguageStats:
    """Statistics for a specific programming language in the repository."""

    language: Language
    file_count: int = 0
    total_lines: int = 0
    total_bytes: int = 0


@dataclass
class FileStats:
    """File-level statistics for a repository."""

    total_files: int = 0
    supported_files: int = 0
    ignored_files: int = 0
    total_bytes: int = 0
    total_lines: int = 0


@dataclass
class RepositoryStats:
    """Comprehensive aggregated statistics for a repository."""

    file_stats: FileStats = field(default_factory=FileStats)
    language_breakdown: Dict[str, LanguageStats] = field(default_factory=dict)
    ignored_files_count: int = 0
    ignored_directories_count: int = 0
