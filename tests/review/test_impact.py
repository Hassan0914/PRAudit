"""Unit tests for Phase 13: Change Impact Analysis Engine."""

from app.git.pr_models import ChangeTypeEnum, DiffHunk, LineChange, PullRequest, PullRequestFile
from app.graphs.models import Edge, Graph, Node, NodeType, RelationType, RepositoryGraphs
from app.review.impact import ChangeImpactEngine
from app.symbols.index import SymbolIndex
from app.symbols.models import Symbol, SymbolKind, SymbolLocation


def test_change_impact_analysis() -> None:
    """Test ChangeImpactEngine downstream caller traversal."""
    # Setup graphs
    call_g = Graph("call_graph")
    call_g.add_node(Node(id="func_a", label="func_a", node_type=NodeType.FUNCTION))
    call_g.add_edge(Edge("caller_b", "func_a", RelationType.CALLS))
    call_g.add_edge(Edge("caller_c", "caller_b", RelationType.CALLS))

    graphs = RepositoryGraphs(call_graph=call_g)

    index = SymbolIndex()
    index.add_symbol(
        Symbol(
            symbol_id="func_a",
            name="func_a",
            kind=SymbolKind.FUNCTION,
            file_path="src/a.py",
            language="python",
            location=SymbolLocation(file_path="src/a.py", start_line=1, end_line=10, start_column=1, end_column=10),
        )
    )
    index.add_symbol(
        Symbol(
            symbol_id="caller_b",
            name="caller_b",
            kind=SymbolKind.FUNCTION,
            file_path="src/b.py",
            language="python",
            location=SymbolLocation(file_path="src/b.py", start_line=1, end_line=10, start_column=1, end_column=10),
        )
    )

    pr = PullRequest(
        pr_id="PR-10",
        title="Impact test",
        description="",
        base_branch="main",
        head_branch="patch",
        base_commit="111",
        head_commit="222",
        files=[
            PullRequestFile(
                file_path="src/a.py",
                change_type=ChangeTypeEnum.MODIFIED,
                hunks=[
                    DiffHunk(
                        old_start_line=1,
                        old_line_count=5,
                        new_start_line=1,
                        new_line_count=5,
                        line_changes=[
                            LineChange(line_number=5, enclosing_symbol="func_a", enclosing_symbol_id="func_a")
                        ],
                    )
                ],
            )
        ],
    )

    engine = ChangeImpactEngine()
    report = engine.analyze_impact(pr, graphs, index, max_depth=3)

    assert report.pr_id == "PR-10"
    assert "src/a.py" in report.impacted_files
    assert report.statistics.downstream_callers_count >= 1
