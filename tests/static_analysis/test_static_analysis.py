"""Unit tests for Phase 9: Static Analysis Engine."""

from pathlib import Path
from app.parsing.service import ParsingEngine
from app.repository.discovery import RepositoryDiscoveryEngine
from app.static_analysis.registry import StaticAnalysisEngine


def test_static_analysis_execution(temp_repo: Path) -> None:
    """Test running static analysis analyzers and building report."""
    discovery = RepositoryDiscoveryEngine()
    parser = ParsingEngine()
    sa_engine = StaticAnalysisEngine()

    metadata, files, stats = discovery.discover(temp_repo)
    parse_results = [parser.parse_file(sf) for sf in files if sf.is_supported]

    report = sa_engine.run_analysis(temp_repo, files, parse_results)

    assert report is not None
    assert len(report.analyzer_results) == 3  # Ruff, MyPy, ESLint
    assert all(res.is_success for res in report.analyzer_results)

    # Check findings detected from malformed/untyped code in sample repo
    assert report.total_findings >= 1
    names = {res.analyzer_name for res in report.analyzer_results}
    assert "ruff" in names
    assert "mypy" in names
    assert "eslint" in names
