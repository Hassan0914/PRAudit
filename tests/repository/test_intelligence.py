"""Unit tests for Phase 5: Repository Intelligence Foundation."""

from pathlib import Path
from app.repository.intelligence import RepositoryIntelligenceEngine


def test_repository_intelligence_end_to_end(temp_repo: Path) -> None:
    """Test complete repository intelligence analysis on temporary repository."""
    engine = RepositoryIntelligenceEngine()
    result = engine.analyze_repository(temp_repo)

    assert result.metadata.name == "sample_repo"
    assert len(result.source_files) > 0
    assert len(result.parse_results) > 0
    assert len(result.chunks) > 0

    # Summary verification
    assert result.summary["repository_name"] == "sample_repo"
    assert result.summary["total_files"] >= 3
    assert result.summary["total_chunks"] >= 4
    assert result.summary["total_symbols"] >= 5

    # Stats verification
    assert result.parsing_stats.total_files_parsed > 0
    assert result.parsing_stats.successful_parses > 0
    assert result.chunk_stats.total_chunks > 0
    assert result.symbol_stats.total_symbols > 0
