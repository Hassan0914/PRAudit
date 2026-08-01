"""Repository Discovery Engine.

Discovers repository files, parses ignore specs, detects languages,
and computes repository metadata and statistics.
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pathspec

from app.core.config import settings
from app.core.exceptions import InvalidRepositoryError, RepositoryNotFoundError
from app.core.logging import setup_logger
from app.core.types import Language
from app.repository.models import (
    FileStats,
    LanguageStats,
    RepositoryMetadata,
    RepositoryStats,
    SourceFile,
)

logger = setup_logger("repository.discovery")


class RepositoryDiscoveryEngine:
    """Engine responsible for scanning, discovering, and analyzing repository structures."""

    def __init__(
        self,
        custom_ignore_patterns: Optional[Set[str]] = None,
        supported_languages: Optional[Set[Language]] = None,
        max_file_size_bytes: Optional[int] = None,
    ) -> None:
        """Initialize the discovery engine.

        Args:
            custom_ignore_patterns: Custom patterns to ignore during file discovery.
            supported_languages: Set of supported languages to filter. Defaults to all recognized languages.
            max_file_size_bytes: Maximum file size to scan. Files larger will be marked unsupported.
        """
        self.ignore_patterns: Set[str] = set(settings.DEFAULT_IGNORE_PATTERNS)
        if custom_ignore_patterns:
            self.ignore_patterns.update(custom_ignore_patterns)

        self.supported_languages = supported_languages
        self.max_file_size_bytes = max_file_size_bytes or settings.MAX_FILE_SIZE_BYTES

    def validate_repository_path(self, repo_path: Path) -> Path:
        """Validate that a given path exists and is a valid directory.

        Args:
            repo_path: Target repository path.

        Returns:
            Resolved absolute Path.

        Raises:
            RepositoryNotFoundError: If the path does not exist.
            InvalidRepositoryError: If the path is not a directory.
        """
        resolved_path = repo_path.resolve()
        if not resolved_path.exists():
            logger.error("Repository path does not exist: %s", repo_path)
            raise RepositoryNotFoundError(f"Repository path does not exist: {repo_path}")

        if not resolved_path.is_dir():
            logger.error("Repository path is not a directory: %s", repo_path)
            raise InvalidRepositoryError(f"Repository path is not a directory: {repo_path}")

        return resolved_path

    def detect_git_repository(self, repo_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if target path is a Git repository and extract HEAD commit if available.

        Args:
            repo_path: Resolved target repository path.

        Returns:
            Tuple of (is_git_repository, head_commit_sha).
        """
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            return False, None

        head_commit: Optional[str] = None
        head_file = git_dir / "HEAD"
        try:
            if head_file.exists() and head_file.is_file():
                head_content = head_file.read_text(encoding="utf-8", errors="ignore").strip()
                if head_content.startswith("ref:"):
                    ref_path = git_dir / head_content.split(":", 1)[1].strip()
                    if ref_path.exists() and ref_path.is_file():
                        head_commit = ref_path.read_text(encoding="utf-8", errors="ignore").strip()
                else:
                    head_commit = head_content
        except Exception as exc:
            logger.warning("Failed to read Git HEAD commit from %s: %s", git_dir, exc)

        return True, head_commit

    def load_ignore_spec(self, repo_path: Path) -> pathspec.PathSpec:
        """Load `.gitignore` and default patterns into a PathSpec object.

        Args:
            repo_path: Target repository path.

        Returns:
            PathSpec instance matching files to ignore.
        """
        patterns: List[str] = list(self.ignore_patterns)

        gitignore_path = repo_path / ".gitignore"
        if gitignore_path.exists() and gitignore_path.is_file():
            try:
                content = gitignore_path.read_text(encoding="utf-8", errors="ignore")
                patterns.extend(content.splitlines())
            except Exception as exc:
                logger.warning("Failed to read .gitignore at %s: %s", gitignore_path, exc)

        return pathspec.PathSpec.from_lines("gitignore", patterns)

    def discover(self, repo_path: Path) -> Tuple[RepositoryMetadata, List[SourceFile], RepositoryStats]:
        """Recursively scan a repository and discover all source files.

        Args:
            repo_path: Target directory path to scan.

        Returns:
            Tuple containing (RepositoryMetadata, List[SourceFile], RepositoryStats).
        """
        resolved_root = self.validate_repository_path(repo_path)
        is_git, head_commit = self.detect_git_repository(resolved_root)
        ignore_spec = self.load_ignore_spec(resolved_root)

        metadata = RepositoryMetadata(
            root_path=resolved_root,
            name=resolved_root.name,
            is_git_repository=is_git,
            git_head_commit=head_commit,
            discovered_at_utc=datetime.now(timezone.utc).isoformat(),
        )

        discovered_files: List[SourceFile] = []
        ignored_files_count = 0
        ignored_dirs_count = 0

        language_map: Dict[str, LanguageStats] = {}
        total_bytes = 0
        total_lines = 0
        supported_count = 0

        for root, dirs, files in os.walk(resolved_root, topdown=True):
            current_root = Path(root)
            rel_root = current_root.relative_to(resolved_root)

            # Filter directories in-place using ignore_spec & hardcoded hidden/venv checks
            filtered_dirs = []
            for d in dirs:
                rel_dir_path = (rel_root / d).as_posix()
                # Check for hidden or common virtualenv/cache directory patterns
                if d.startswith(".") or d in {"__pycache__", "node_modules", "dist", "build", "venv", ".venv", "env"}:
                    ignored_dirs_count += 1
                    continue
                if ignore_spec.match_file(rel_dir_path) or ignore_spec.match_file(rel_dir_path + "/"):
                    ignored_dirs_count += 1
                    continue
                filtered_dirs.append(d)
            dirs[:] = filtered_dirs

            for file_name in files:
                rel_file_path = (rel_root / file_name).as_posix() if rel_root != Path(".") else file_name
                abs_file_path = current_root / file_name

                # Skip hidden files or ignored patterns
                if file_name.startswith(".") or ignore_spec.match_file(rel_file_path):
                    ignored_files_count += 1
                    continue

                ext = abs_file_path.suffix.lower()
                lang = Language.from_extension(ext)

                try:
                    file_size = abs_file_path.stat().st_size
                except OSError as err:
                    logger.warning("Could not stat file %s: %s", abs_file_path, err)
                    ignored_files_count += 1
                    continue

                is_supported = True
                if file_size > self.max_file_size_bytes:
                    is_supported = False

                if self.supported_languages and lang not in self.supported_languages:
                    is_supported = False

                lines_count, content_hash = self._analyze_file_content(abs_file_path)

                source_file = SourceFile(
                    relative_path=rel_file_path,
                    absolute_path=abs_file_path,
                    extension=ext,
                    language=lang,
                    size_bytes=file_size,
                    line_count=lines_count,
                    is_supported=is_supported,
                    content_hash=content_hash,
                )

                discovered_files.append(source_file)

                total_bytes += file_size
                total_lines += lines_count

                if is_supported:
                    supported_count += 1

                # Aggregate language statistics
                lang_key = lang.value
                if lang_key not in language_map:
                    language_map[lang_key] = LanguageStats(language=lang)
                lang_stats = language_map[lang_key]
                lang_stats.file_count += 1
                lang_stats.total_lines += lines_count
                lang_stats.total_bytes += file_size

        file_stats = FileStats(
            total_files=len(discovered_files),
            supported_files=supported_count,
            ignored_files=ignored_files_count,
            total_bytes=total_bytes,
            total_lines=total_lines,
        )

        repo_stats = RepositoryStats(
            file_stats=file_stats,
            language_breakdown=language_map,
            ignored_files_count=ignored_files_count,
            ignored_directories_count=ignored_dirs_count,
        )

        logger.info(
            "Discovered %d files (%d supported, %d ignored) across %d languages in repository %s",
            len(discovered_files),
            supported_count,
            ignored_files_count,
            len(language_map),
            resolved_root.name,
        )

        return metadata, discovered_files, repo_stats

    def _analyze_file_content(self, file_path: Path) -> Tuple[int, Optional[str]]:
        """Safely read file lines count and compute SHA-256 content hash.

        Args:
            file_path: Path to the target file.

        Returns:
            Tuple of (line_count, SHA-256 content hash).
        """
        try:
            content_bytes = file_path.read_bytes()
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            # Attempt string decoding for line count
            text = content_bytes.decode("utf-8", errors="ignore")
            lines_count = len(text.splitlines()) if text else 0
            return lines_count, content_hash
        except Exception as exc:
            logger.debug("Failed to read file content for stats at %s: %s", file_path, exc)
            return 0, None
