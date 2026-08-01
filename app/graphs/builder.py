"""Relationship Engine orchestrating call, import, dependency, and inheritance graphs."""

from typing import List
from app.core.logging import setup_logger
from app.graphs.call_graph import CallGraphBuilder
from app.graphs.import_graph import ImportGraphBuilder
from app.graphs.inheritance_graph import InheritanceGraphBuilder
from app.graphs.models import RepositoryGraphs
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.symbols.index import SymbolIndex

logger = setup_logger("graphs.builder")


class RelationshipEngine:
    """Master engine for building repository graphs."""

    def __init__(self) -> None:
        """Initialize relationship engine builders."""
        self.call_builder = CallGraphBuilder()
        self.import_builder = ImportGraphBuilder()
        self.inheritance_builder = InheritanceGraphBuilder()

    def build_all_graphs(
        self,
        source_files: List[SourceFile],
        parse_results: List[ParseResult],
        symbol_index: SymbolIndex,
    ) -> RepositoryGraphs:
        """Build call graph, import graph, dependency graph, and inheritance graph.

        Args:
            source_files: List of discovered source files.
            parse_results: List of AST parse results.
            symbol_index: Indexed symbols.

        Returns:
            RepositoryGraphs object containing all graphs.
        """
        logger.info("Building repository relationship graphs...")

        call_g = self.call_builder.build_call_graph(parse_results, symbol_index)
        import_g = self.import_builder.build_import_graph(source_files, symbol_index)
        dep_g = self.import_builder.build_dependency_graph(import_g)
        inher_g = self.inheritance_builder.build_inheritance_graph(parse_results, symbol_index)

        logger.info(
            "Repository relationship graphs built successfully: Call (%d nodes), Import (%d nodes), Dependency (%d nodes), Inheritance (%d nodes).",
            len(call_g.nodes),
            len(import_g.nodes),
            len(dep_g.nodes),
            len(inher_g.nodes),
        )

        return RepositoryGraphs(
            call_graph=call_g,
            import_graph=import_g,
            dependency_graph=dep_g,
            inheritance_graph=inher_g,
        )
