"""Unit tests for Phase 11: Git Integration Engine."""

from pathlib import Path
from app.git.service import GitBranchService, GitCommitService, GitRepositoryService


def test_git_repository_service(temp_repo: Path) -> None:
    """Test getting Git repository status and branch."""
    repo_service = GitRepositoryService()
    state = repo_service.get_repository_state(temp_repo)

    assert state is not None
    assert state.current_branch in {"main", "master", "HEAD"}
    assert state.head_commit is not None


def test_git_commit_history(temp_repo: Path) -> None:
    """Test retrieving commit history."""
    commit_service = GitCommitService()
    commits = commit_service.get_commit_history(temp_repo, max_count=5)

    assert len(commits) >= 1
    assert commits[0].hash is not None
    assert commits[0].author_name is not None


def test_git_branches(temp_repo: Path) -> None:
    """Test listing branches."""
    branch_service = GitBranchService()
    branches = branch_service.get_branches(temp_repo)

    assert len(branches) >= 1
    assert any(b.is_head for b in branches)
