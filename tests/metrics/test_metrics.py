"""Unit tests for Phase 8: Code Metrics Engine."""

from pathlib import Path
from app.core.types import Language
from app.metrics.calculator import MetricsEngine
from app.parsing.service import ParsingEngine
from app.repository.discovery import RepositoryDiscoveryEngine
from app.repository.models import SourceFile


def test_metrics_calculator(temp_repo: Path) -> None:
    """Test evaluating function, file, and repository metrics."""
    discovery = RepositoryDiscoveryEngine()
    parser = ParsingEngine()
    metrics_engine = MetricsEngine()

    metadata, files, stats = discovery.discover(temp_repo)
    parse_results = [parser.parse_file(sf) for sf in files if sf.is_supported]

    repo_metrics = metrics_engine.analyze_repository_metrics(files, parse_results)

    assert repo_metrics.total_files == len(files)
    assert repo_metrics.total_lines > 0
    assert repo_metrics.total_code_lines > 0
    assert repo_metrics.average_cyclomatic_complexity >= 1.0
    assert repo_metrics.average_maintainability_index > 0.0

    # Inspect specific file metrics
    fm = repo_metrics.file_metrics.get("src/main.py")
    assert fm is not None
    assert fm.total_lines > 0
    assert len(fm.functions) >= 1
    assert len(fm.classes) >= 1


def test_cyclomatic_complexity_calculation() -> None:
    """Test AST complexity calculation on branching code."""
    code = (
        "def complex_func(x):\n"
        "    if x > 10:\n"
        "        if x > 20:\n"
        "            return 2\n"
        "        return 1\n"
        "    elif x < 0:\n"
        "        return -1\n"
        "    return 0\n"
    )
    parser = ParsingEngine()
    metrics_engine = MetricsEngine()

    parse_res = parser.parse_code(code, Language.PYTHON, "complex.py")
    fm = metrics_engine.analyze_file_metrics(
        SourceFile(
            relative_path="complex.py",
            absolute_path=Path("complex.py"),
            extension=".py",
            language=Language.PYTHON,
            size_bytes=len(code),
            line_count=8,
        ),
        parse_res,
    )

    assert len(fm.functions) == 1
    fn = fm.functions[0]
    assert fn.name == "complex_func"
    assert fn.cyclomatic_complexity >= 3  # 1 base + if + if + elif
    assert fn.max_nesting_depth >= 2
