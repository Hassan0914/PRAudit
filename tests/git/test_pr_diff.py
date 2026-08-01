"""Unit tests for Phase 12: Pull Request Diff Engine."""

from app.git.diff_parser import PRDiffParser
from app.git.mapper import DiffSymbolMapper
from app.git.pr_models import ChangeTypeEnum, PullRequest
from app.symbols.index import SymbolIndex
from app.symbols.models import Symbol, SymbolKind, SymbolLocation


def test_parse_unified_diff() -> None:
    """Test PRDiffParser parsing raw unified diff string."""
    raw_diff = (
        "diff --git a/src/main.py b/src/main.py\n"
        "index 1234567..89abcdef 100644\n"
        "--- a/src/main.py\n"
        "+++ b/src/main.py\n"
        "@@ -5,6 +5,8 @@\n"
        " def add(a, b):\n"
        "+    # Added comment\n"
        "+    result = a + b\n"
        "     return a + b\n"
    )
    parser = PRDiffParser()
    files = parser.parse_diff(raw_diff)

    assert len(files) == 1
    f = files[0]
    assert f.file_path == "src/main.py"
    assert len(f.hunks) == 1
    assert f.added_lines_count == 2
    assert f.deleted_lines_count == 0


def test_diff_symbol_mapper() -> None:
    """Test DiffSymbolMapper mapping line changes to enclosing symbols."""
    raw_diff = (
        "diff --git a/src/main.py b/src/main.py\n"
        "--- a/src/main.py\n"
        "+++ b/src/main.py\n"
        "@@ -10,3 +10,4 @@\n"
        "+    new_code = True\n"
    )
    parser = PRDiffParser()
    files = parser.parse_diff(raw_diff)

    pr = PullRequest(
        pr_id="PR-1",
        title="Test PR",
        description="",
        base_branch="main",
        head_branch="feature",
        base_commit="abc",
        head_commit="def",
        files=files,
    )

    index = SymbolIndex()
    index.add_symbol(
        Symbol(
            symbol_id="sym_calculate",
            name="calculate",
            kind=SymbolKind.FUNCTION,
            file_path="src/main.py",
            language="python",
            location=SymbolLocation(file_path="src/main.py", start_line=5, end_line=20, start_column=1, end_column=20),
        )
    )

    mapper = DiffSymbolMapper()
    mapped_pr = mapper.map_pr_symbols(pr, index)

    lc = mapped_pr.files[0].hunks[0].line_changes[0]
    assert lc.enclosing_symbol == "calculate"
    assert lc.enclosing_symbol_id == "sym_calculate"
