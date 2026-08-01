"""High-level Git services exposing repository status, commits, branches, and diffs."""

from pathlib import Path
from typing import List, Optional

from app.core.logging import setup_logger
from app.git.adapter import BaseGitAdapter, SubprocessGitAdapter
from app.git.models import Branch, Commit, GitDiff, RepositoryState

logger = setup_logger("git.service")


class GitRepositoryService:
    """Service providing Git repository status and workspace information."""

    def __init__(self, adapter: Optional[BaseGitAdapter] = None) -> None:
        self.adapter = adapter or SubprocessGitAdapter()

    def get_repository_state(self, repo_path: Path) -> RepositoryState:
        """Get repository working tree state.

        Args:
            repo_path: Target repository path.

        Returns:
            RepositoryState model.
        """
        return self.adapter.get_status(repo_path)


class GitCommitService:
    """Service providing Git commit history retrieval."""

    def __init__(self, adapter: Optional[BaseGitAdapter] = None) -> None:
        self.adapter = adapter or SubprocessGitAdapter()

    def get_commit_history(self, repo_path: Path, max_count: int = 50) -> List[Commit]:
        """Get commit history.

        Args:
            repo_path: Target repository path.
            max_count: Maximum commit count.

        Returns:
            List of Commit objects.
        """
        return self.adapter.get_commits(repo_path, max_count=max_count)


class GitBranchService:
    """Service providing branch listing and tracking."""

    def __init__(self, adapter: Optional[BaseGitAdapter] = None) -> None:
        self.adapter = adapter or SubprocessGitAdapter()

    def get_branches(self, repo_path: Path) -> List[Branch]:
        """Get repository branches.

        Args:
            repo_path: Target repository path.

        Returns:
            List of Branch objects.
        """
        return self.adapter.get_branches(repo_path)


class GitDiffService:
    """Service providing diff calculation and file change retrieval."""

    def __init__(self, adapter: Optional[BaseGitAdapter] = None) -> None:
        self.adapter = adapter or SubprocessGitAdapter()

    def get_diff(self, repo_path: Path, base_ref: str, head_ref: str) -> GitDiff:
        """Get Git diff between two refs.

        Args:
            repo_path: Target repository path.
            base_ref: Base commit/branch ref.
            head_ref: Head commit/branch ref.

        Returns:
            GitDiff model.
        """
        return self.adapter.get_diff(repo_path, base_ref, head_ref)
