"""Data models for Pull Request diff parsing and line-to-symbol mappings."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ChangeTypeEnum(str, Enum):
    """Types of file or line changes in a Pull Request."""

    ADDED = "ADDED"
    DELETED = "DELETED"
    MODIFIED = "MODIFIED"
    RENAMED = "RENAMED"
    UNCHANGED = "UNCHANGED"


@dataclass
class LineChange:
    """Represents a single changed line in a PR diff."""

    line_number: int              # New file line number if ADDED/MODIFIED, old if DELETED
    old_line_number: Optional[int] = None
    change_type: ChangeTypeEnum = ChangeTypeEnum.MODIFIED
    content: str = ""
    enclosing_symbol: Optional[str] = None    # Symbol Name
    enclosing_symbol_id: Optional[str] = None # Symbol ID
    enclosing_function: Optional[str] = None  # Function Name
    enclosing_class: Optional[str] = None     # Class Name


@dataclass
class DiffHunk:
    """Represents a single hunk in a unified Git diff."""

    old_start_line: int
    old_line_count: int
    new_start_line: int
    new_line_count: int
    header: str = ""
    line_changes: List[LineChange] = field(default_factory=list)


@dataclass
class PullRequestFile:
    """Represents a changed file within a Pull Request."""

    file_path: str
    old_path: Optional[str] = None
    change_type: ChangeTypeEnum = ChangeTypeEnum.MODIFIED
    hunks: List[DiffHunk] = field(default_factory=list)
    added_lines_count: int = 0
    deleted_lines_count: int = 0
    is_binary: bool = False


@dataclass
class PullRequest:
    """Represents a complete Pull Request containing modified files and metadata."""

    pr_id: str
    title: str
    description: str
    base_branch: str
    head_branch: str
    base_commit: str
    head_commit: str
    files: List[PullRequestFile] = field(default_factory=list)
    author: str = "author"
    created_at: str = ""
