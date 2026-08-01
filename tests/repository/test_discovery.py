"""Unit tests for Phase 1: Repository Discovery Engine."""

from pathlib import Path
import pytest
from app.core.exceptions import InvalidRepositoryError, RepositoryNotFoundError
from app.core.types import Language
from app.repository.discovery import RepositoryDiscoveryEngine


def test_validate_repository_path_success(temp_repo: Path) -> None:
    """Test validating an existing valid directory."""
    engine = RepositoryDiscoveryEngine()
    resolved = engine.validate_repository_path(temp_repo)
    assert resolved == temp_repo.resolve()


def test_validate_repository_path_not_found(tmp_path: Path) -> None:
    """Test validating a non-existent path raises RepositoryNotFoundError."""
    engine = RepositoryDiscoveryEngine()
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(RepositoryNotFoundError):
        engine.validate_repository_path(non_existent)


def test_validate_repository_path_not_a_directory(temp_repo: Path) -> None:
    """Test validating a file path raises InvalidRepositoryError."""
    engine = RepositoryDiscoveryEngine()
    file_path = temp_repo / "src" / "main.py"
    with pytest.raises(InvalidRepositoryError):
        engine.validate_repository_path(file_path)


def test_detect_git_repository(temp_repo: Path) -> None:
    """Test Git repository detection and HEAD commit extraction."""
    engine = RepositoryDiscoveryEngine()
    is_git, head_commit = engine.detect_git_repository(temp_repo)
    assert is_git is True
    assert head_commit == "1234567890abcdef1234567890abcdef12345678"


def test_discover_repository_files(temp_repo: Path) -> None:
    """Test full repository discovery scanning."""
    engine = RepositoryDiscoveryEngine()
    metadata, files, stats = engine.discover(temp_repo)

    assert metadata.name == "sample_repo"
    assert metadata.is_git_repository is True

    rel_paths = [f.relative_path for f in files]
    assert "src/main.py" in rel_paths
    assert "src/utils.js" in rel_paths
    assert "src/bad.py" in rel_paths

    # Verify ignored files
    assert "app.log" not in rel_paths
    assert "ignore_me/temp.txt" not in rel_paths

    # Check stats
    assert stats.file_stats.total_files == len(files)
    assert "python" in stats.language_breakdown
    assert "javascript" in stats.language_breakdown
