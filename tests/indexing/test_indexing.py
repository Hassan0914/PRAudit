"""Unit tests for Phase 7: Repository Indexing Engine."""

from pathlib import Path
from app.chunking.service import ChunkingService
from app.indexing.service import IndexingService
from app.parsing.service import ParsingEngine
from app.repository.discovery import RepositoryDiscoveryEngine
from app.symbols.service import SymbolService


def test_unified_repository_index_search(temp_repo: Path) -> None:
    """Test indexing files, symbols, chunks and performing prefix search."""
    discovery = RepositoryDiscoveryEngine()
    parser = ParsingEngine()
    chunker = ChunkingService()
    symbol_service = SymbolService()
    indexing_service = IndexingService()

    metadata, files, stats = discovery.discover(temp_repo)
    parse_results = [parser.parse_file(sf) for sf in files if sf.is_supported]

    all_chunks = []
    all_symbols = []
    for sf, pr in zip(files, parse_results):
        all_chunks.extend(chunker.extract_chunks_from_file(sf, pr))
        all_symbols.extend(symbol_service.extract_symbols_from_file(sf, pr))

    index = indexing_service.build_index(files, all_symbols, all_chunks)
    index_stats = index.compute_stats()

    assert index_stats.indexed_files_count > 0
    assert index_stats.indexed_symbols_count > 0
    assert index_stats.indexed_chunks_count > 0

    # Test prefix search
    res = indexing_service.search("add")
    assert res.total_matches > 0
    assert any(s.name == "add" for s in res.symbols)

    # Test lookup by file
    main_syms = index.get_symbols_by_file("src/main.py")
    assert len(main_syms) > 0
