"""Subprocess-backed Git adapter isolating Git CLI execution."""

from abc import ABC, abstractmethod
from pathlib import Path
import subprocess
from typing import List, Optional

from app.core.exceptions import PRAuditError
from app.core.logging import setup_logger
from app.git.models import (
    Branch,
    ChangeType,
    Commit,
    GitDiff,
    GitFileChange,
    RepositoryState,
)

logger = setup_logger("git.adapter")


class BaseGitAdapter(ABC):
    """Abstract adapter interface for Git operations."""

    @abstractmethod
    def get_status(self, repo_path: Path) -> RepositoryState:
        """Get repository working tree status."""
        pass

    @abstractmethod
    def get_commits(self, repo_path: Path, max_count: int = 50) -> List[Commit]:
        """Get commit history."""
        pass

    @abstractmethod
    def get_branches(self, repo_path: Path) -> List[Branch]:
        """Get local and remote branches."""
        pass

    @abstractmethod
    def get_merge_base(self, repo_path: Path, base_ref: str, head_ref: str) -> Optional[str]:
        """Lookup merge base commit between two refs."""
        pass

    @abstractmethod
    def get_diff(self, repo_path: Path, base_ref: str, head_ref: str) -> GitDiff:
        """Get Git diff between two refs."""
        pass


class SubprocessGitAdapter(BaseGitAdapter):
    """Git adapter implementation executing Git CLI binary via subprocess."""

    def _run_git(self, repo_path: Path, args: List[str]) -> str:
        """Run a git command in target repo path.

        Args:
            repo_path: Target repository path.
            args: Command arguments list.

        Returns:
            Standard output text string.
        """
        try:
            cmd = ["git"] + args
            proc = subprocess.run(
                cmd, cwd=str(repo_path), capture_output=True, text=True, errors="ignore", check=True
            )
            return proc.stdout.strip()
        except subprocess.CalledProcessError as exc:
            err_msg = exc.stderr.strip() or str(exc)
            logger.debug("Git command failed 'git %s': %s", " ".join(args), err_msg)
            raise PRAuditError(f"Git command failed: git {' '.join(args)} | {err_msg}") from exc
        except Exception as exc:
            logger.error("Failed to execute git command: %s", exc)
            raise PRAuditError(f"Git execution error: {exc}") from exc

    def get_status(self, repo_path: Path) -> RepositoryState:
        """Get current branch and status."""
        branch = self._run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        status_out = self._run_git(repo_path, ["status", "--porcelain"])

        staged = []
        unstaged = []
        untracked = []

        for line in status_out.splitlines():
            if len(line) < 3:
                continue
            x = line[0]
            y = line[1]
            path_str = line[3:].strip()

            if x in {"M", "A", "D", "R"}:
                staged.append(path_str)
            if y in {"M", "D"}:
                unstaged.append(path_str)
            if x == "?" and y == "?":
                untracked.append(path_str)

        commits = self.get_commits(repo_path, max_count=1)
        head_commit = commits[0] if commits else None
        is_dirty = bool(staged or unstaged or untracked)

        return RepositoryState(
            current_branch=branch,
            head_commit=head_commit,
            is_dirty=is_dirty,
            staged_files=staged,
            unstaged_files=unstaged,
            untracked_files=untracked,
        )

    def get_commits(self, repo_path: Path, max_count: int = 50) -> List[Commit]:
        """Get commit history log."""
        fmt = "%H%n%h%n%an%n%ae%n%aI%n%s%n%P%n---"
        raw_log = self._run_git(repo_path, ["log", f"-n{max_count}", f"--format={fmt}"])
        commits: List[Commit] = []

        if not raw_log:
            return commits

        blocks = raw_log.split("---\n")
        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) >= 6:
                c_hash = lines[0]
                short_hash = lines[1]
                author = lines[2]
                email = lines[3]
                date_str = lines[4]
                msg = lines[5]
                parents = lines[6].split() if len(lines) > 6 and lines[6].strip() else []

                commits.append(
                    Commit(
                        hash=c_hash,
                        short_hash=short_hash,
                        author_name=author,
                        author_email=email,
                        committed_at=date_str,
                        message=msg,
                        parents=parents,
                    )
                )

        return commits

    def get_branches(self, repo_path: Path) -> List[Branch]:
        """Get list of local branches."""
        out = self._run_git(repo_path, ["branch", "-v", "--no-color"])
        branches: List[Branch] = []

        for line in out.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            is_head = line_str.startswith("*")
            clean_line = line_str.lstrip("* ").strip()
            parts = clean_line.split()

            if len(parts) >= 2:
                name = parts[0]
                commit_h = parts[1]
                branches.append(Branch(name=name, commit_hash=commit_h, is_head=is_head))

        return branches

    def get_merge_base(self, repo_path: Path, base_ref: str, head_ref: str) -> Optional[str]:
        """Lookup merge base SHA between base_ref and head_ref."""
        try:
            return self._run_git(repo_path, ["merge-base", base_ref, head_ref])
        except Exception:
            return None

    def get_diff(self, repo_path: Path, base_ref: str, head_ref: str) -> GitDiff:
        """Get diff between base_ref and head_ref."""
        merge_base = self.get_merge_base(repo_path, base_ref, head_ref)
        target_base = merge_base or base_ref

        raw_diff = self._run_git(repo_path, ["diff", f"{target_base}..{head_ref}"])
        numstat = self._run_git(repo_path, ["diff", "--numstat", f"{target_base}..{head_ref}"])

        file_changes: List[GitFileChange] = []
        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                added_str, deleted_str, path_str = parts
                is_bin = added_str == "-" or deleted_str == "-"
                add_c = int(added_str) if not is_bin else 0
                del_c = int(deleted_str) if not is_bin else 0

                file_changes.append(
                    GitFileChange(
                        relative_path=path_str,
                        change_type=ChangeType.MODIFIED,
                        lines_added=add_c,
                        lines_deleted=del_c,
                        is_binary=is_bin,
                    )
                )

        return GitDiff(
            base_ref=base_ref,
            head_ref=head_ref,
            merge_base=merge_base,
            file_changes=file_changes,
            raw_diff=raw_diff,
        )
