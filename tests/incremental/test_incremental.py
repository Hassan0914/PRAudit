"""Unit tests for Phase 24: Incremental Analysis Engine."""

from pathlib import Path
from app.git.pr_models import ChangeTypeEnum, DiffHunk, LineChange, PullRequest, PullRequestFile
from app.incremental.service import IncrementalAnalysisEngine
from app.repository.intelligence import RepositoryIntelligenceEngine


def test_incremental_analysis_engine(temp_repo: Path) -> None:
    intel_engine = RepositoryIntelligenceEngine()
    intel = intel_engine.analyze_repository(temp_repo)

    pr = PullRequest(
        pr_id="PR-INC-1",
        title="Incremental test",
        description="",
        base_branch="main",
        head_branch="dev",
        base_commit="111",
        head_commit="222",
        files=[
            PullRequestFile(
                file_path="src/main.py",
                change_type=ChangeTypeEnum.MODIFIED,
                hunks=[
                    DiffHunk(
                        old_start_line=1,
                        old_line_count=5,
                        new_start_line=1,
                        new_line_count=5,
                        line_changes=[LineChange(line_number=5, content="def add(a, b): return a + b")],
                    )
                ],
            )
        ],
    )

    inc_engine = IncrementalAnalysisEngine()
    report = inc_engine.analyze_delta(pr, intel)

    assert report.pr_id == "PR-INC-1"
    assert report.changed_files_count == 1
    assert len(report.affected_symbols) >= 1
