"""Parser converting raw Git unified diff text into structured PR models."""

import re
from typing import List, Optional
from app.core.logging import setup_logger
from app.git.pr_models import ChangeTypeEnum, DiffHunk, LineChange, PullRequestFile

logger = setup_logger("git.diff_parser")


class PRDiffParser:
    """Parser for unified Git diffs."""

    HUNK_HEADER_PATTERN = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

    def parse_diff(self, raw_diff: str) -> List[PullRequestFile]:
        """Parse raw unified diff text into a list of PullRequestFile objects.

        Args:
            raw_diff: Raw git diff output string.

        Returns:
            List of PullRequestFile objects.
        """
        pr_files: List[PullRequestFile] = []
        if not raw_diff or not raw_diff.strip():
            return pr_files

        file_blocks = self._split_diff_into_files(raw_diff)

        for block in file_blocks:
            pr_file = self._parse_file_block(block)
            if pr_file:
                pr_files.append(pr_file)

        logger.debug("Parsed diff into %d changed files", len(pr_files))
        return pr_files

    def _split_diff_into_files(self, raw_diff: str) -> List[str]:
        """Split diff text by 'diff --git' headers."""
        blocks: List[str] = []
        curr: List[str] = []

        for line in raw_diff.splitlines():
            if line.startswith("diff --git"):
                if curr:
                    blocks.append("\n".join(curr))
                    curr = []
            curr.append(line)

        if curr:
            blocks.append("\n".join(curr))

        return blocks

    def _parse_file_block(self, block: str) -> Optional[PullRequestFile]:
        """Parse a single file's diff block."""
        lines = block.splitlines()
        if not lines:
            return None

        header_line = lines[0]  # e.g., diff --git a/file1.py b/file2.py
        file_path = ""
        old_path = None
        change_type = ChangeTypeEnum.MODIFIED

        # Extract file paths from diff --git a/path b/path
        parts = header_line.split()
        if len(parts) >= 4:
            old_p = parts[2].lstrip("a/")
            new_p = parts[3].lstrip("b/")
            file_path = new_p
            if old_p != new_p:
                old_path = old_p
                change_type = ChangeTypeEnum.RENAMED

        # Inspect diff status lines
        for line in lines[:10]:
            if line.startswith("new file mode"):
                change_type = ChangeTypeEnum.ADDED
            elif line.startswith("deleted file mode"):
                change_type = ChangeTypeEnum.DELETED

        hunks: List[DiffHunk] = []
        curr_hunk: Optional[DiffHunk] = None

        old_line_no = 0
        new_line_no = 0
        added_count = 0
        deleted_count = 0

        for line in lines:
            if line.startswith("@@"):
                match = self.HUNK_HEADER_PATTERN.match(line)
                if match:
                    old_start = int(match.group(1))
                    old_len = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_len = int(match.group(4)) if match.group(4) else 1

                    curr_hunk = DiffHunk(
                        old_start_line=old_start,
                        old_line_count=old_len,
                        new_start_line=new_start,
                        new_line_count=new_len,
                        header=line,
                        line_changes=[],
                    )
                    hunks.append(curr_hunk)

                    old_line_no = old_start
                    new_line_no = new_start
                    continue

            if curr_hunk is None:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                added_count += 1
                curr_hunk.line_changes.append(
                    LineChange(
                        line_number=new_line_no,
                        old_line_number=None,
                        change_type=ChangeTypeEnum.ADDED,
                        content=line[1:],
                    )
                )
                new_line_no += 1
            elif line.startswith("-") and not line.startswith("---"):
                deleted_count += 1
                curr_hunk.line_changes.append(
                    LineChange(
                        line_number=new_line_no if new_line_no > 0 else old_line_no,
                        old_line_number=old_line_no,
                        change_type=ChangeTypeEnum.DELETED,
                        content=line[1:],
                    )
                )
                old_line_no += 1
            elif line.startswith(" ") or line == "":
                curr_hunk.line_changes.append(
                    LineChange(
                        line_number=new_line_no,
                        old_line_number=old_line_no,
                        change_type=ChangeTypeEnum.UNCHANGED,
                        content=line[1:] if line.startswith(" ") else "",
                    )
                )
                old_line_no += 1
                new_line_no += 1

        if not file_path and len(parts) >= 4:
            file_path = parts[3].lstrip("b/")

        return PullRequestFile(
            file_path=file_path,
            old_path=old_path,
            change_type=change_type,
            hunks=hunks,
            added_lines_count=added_count,
            deleted_lines_count=deleted_count,
        )
