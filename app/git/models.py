"""Data models for Git repositories, commits, branches, and diffs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ChangeType(str, Enum):
    """Types of Git file changes."""

    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNKNOWN = "U"


@dataclass
class GitFileChange:
    """Represents a single file change in a Git commit or diff."""

    relative_path: str
    old_path: Optional[str] = None
    change_type: ChangeType = ChangeType.MODIFIED
    lines_added: int = 0
    lines_deleted: int = 0
    is_binary: bool = False


@dataclass
class Commit:
    """Represents a Git commit."""

    hash: str
    short_hash: str
    author_name: str
    author_email: str
    committed_at: str
    message: str
    parents: List[str] = field(default_factory=list)


@dataclass
class Branch:
    """Represents a Git branch."""

    name: str
    commit_hash: str
    is_head: bool = False
    remote_name: Optional[str] = None


@dataclass
class GitDiff:
    """Container for Git diff information between commits or refs."""

    base_ref: str
    head_ref: str
    merge_base: Optional[str] = None
    file_changes: List[GitFileChange] = field(default_factory=list)
    raw_diff: str = ""


@dataclass
class RepositoryState:
    """Represents current state of a Git repository working tree."""

    current_branch: str
    head_commit: Optional[Commit] = None
    is_dirty: bool = False
    staged_files: List[str] = field(default_factory=list)
    unstaged_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
