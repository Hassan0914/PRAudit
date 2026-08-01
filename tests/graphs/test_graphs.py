"""Unit tests for Phase 6: Repository Relationship Engine."""

from pathlib import Path
from app.graphs.builder import RelationshipEngine
from app.graphs.models import NodeType, RelationType
from app.parsing.service import ParsingEngine
from app.repository.discovery import RepositoryDiscoveryEngine
from app.symbols.service import SymbolService


def test_build_all_graphs(temp_repo: Path) -> None:
    """Test building call, import, dependency, and inheritance graphs."""
    discovery = RepositoryDiscoveryEngine()
    parser = ParsingEngine()
    symbol_service = SymbolService()
    rel_engine = RelationshipEngine()

    metadata, files, stats = discovery.discover(temp_repo)
    parse_results = [parser.parse_file(sf) for sf in files if sf.is_supported]
    for sf, pr in zip(files, parse_results):
        symbol_service.extract_symbols_from_file(sf, pr)

    graphs = rel_engine.build_all_graphs(files, parse_results, symbol_service.index)

    # Call graph assertions
    assert graphs.call_graph.name == "call_graph"
    assert len(graphs.call_graph.nodes) > 0

    # Import graph assertions
    assert graphs.import_graph.name == "import_graph"
    assert len(graphs.import_graph.nodes) > 0

    # Dependency graph assertions
    assert graphs.dependency_graph.name == "dependency_graph"

    # Inheritance graph assertions
    assert graphs.inheritance_graph.name == "inheritance_graph"

    # Test serialization
    call_dict = graphs.call_graph.to_dict()
    assert "nodes" in call_dict
    assert "edges" in call_dict
    assert "stats" in call_dict
