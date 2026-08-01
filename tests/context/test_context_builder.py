"""Unit tests for Phase 17: Context Assembly & Retrieval."""

from pathlib import Path
from app.context.builder import ContextBuilder
from app.git.pr_models import ChangeTypeEnum, DiffHunk, LineChange, PullRequest, PullRequestFile
from app.graphs.models import RepositoryGraphs
from app.repository.intelligence import RepositoryIntelligenceEngine
from app.review.impact import ChangeImpactEngine


def test_context_builder_assembly(temp_repo: Path) -> None:
    """Test ContextBuilder assembling targeted context within token budget."""
    intel_engine = RepositoryIntelligenceEngine()
    intel = intel_engine.analyze_repository(temp_repo)

    pr = PullRequest(
        pr_id="PR-CTX-1",
        title="Context test",
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
                        line_changes=[LineChange(line_number=1, content="def add(a, b): return a + b")],
                    )
                ],
            )
        ],
    )

    impact_engine = ChangeImpactEngine()
    impact_report = impact_engine.analyze_impact(pr, intel.graphs, intel.symbol_index)

    builder = ContextBuilder()
    context_obj = builder.assemble_context(pr, intel, impact_report, token_budget=16000)

    assert context_obj.pr_id == "PR-CTX-1"
    assert len(context_obj.sections) >= 3
    assert context_obj.total_estimated_tokens > 0
    assert not context_obj.is_truncated
