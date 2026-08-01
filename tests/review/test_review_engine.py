"""Unit tests for Phase 14: Deterministic Review Engine."""

from pathlib import Path
from app.git.pr_models import ChangeTypeEnum, DiffHunk, LineChange, PullRequest, PullRequestFile
from app.repository.intelligence import RepositoryIntelligenceEngine
from app.review.engine import DeterministicReviewEngine
from app.review.review_models import ReviewVerdict


def test_deterministic_review_engine(temp_repo: Path) -> None:
    """Test executing deterministic PR review against sample repository."""
    intel_engine = RepositoryIntelligenceEngine()
    intel = intel_engine.analyze_repository(temp_repo)

    pr = PullRequest(
        pr_id="PR-REV-1",
        title="Sample Review PR",
        description="",
        base_branch="main",
        head_branch="dev",
        base_commit="aaa",
        head_commit="bbb",
        files=[
            PullRequestFile(
                file_path="src/main.py",
                change_type=ChangeTypeEnum.MODIFIED,
                hunks=[
                    DiffHunk(
                        old_start_line=1,
                        old_line_count=10,
                        new_start_line=1,
                        new_line_count=10,
                        line_changes=[LineChange(line_number=5, content="def add(a, b): return a + b")],
                    )
                ],
            )
        ],
    )

    review_engine = DeterministicReviewEngine()
    report = review_engine.review_pull_request(pr, intel)

    assert report.review_id is not None
    assert report.pr_id == "PR-REV-1"
    assert report.summary.verdict in {ReviewVerdict.APPROVE, ReviewVerdict.REQUEST_CHANGES, ReviewVerdict.COMMENT}
