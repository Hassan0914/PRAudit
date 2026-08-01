"""Import Graph and Module Dependency Graph builder."""

from typing import Dict, List, Set
from app.core.logging import setup_logger
from app.graphs.models import Edge, Graph, Node, NodeType, RelationType
from app.repository.models import SourceFile
from app.symbols.index import SymbolIndex
from app.symbols.models import SymbolKind

logger = setup_logger("graphs.import_graph")


class ImportGraphBuilder:
    """Builder for constructing import and module dependency graphs."""

    def build_import_graph(
        self, source_files: List[SourceFile], symbol_index: SymbolIndex
    ) -> Graph:
        """Construct an Import Graph mapping module imports.

        Args:
            source_files: List of discovered SourceFile objects.
            symbol_index: Indexed symbols containing import entries.

        Returns:
            Graph instance for import dependencies.
        """
        graph = Graph(name="import_graph")
        known_files: Set[str] = {sf.relative_path for sf in source_files}

        # Add all files as module nodes
        for sf in source_files:
            graph.add_node(
                Node(
                    id=sf.relative_path,
                    label=sf.relative_path,
                    node_type=NodeType.MODULE,
                    file_path=sf.relative_path,
                )
            )

        import_symbols = symbol_index.lookup_by_kind(SymbolKind.IMPORT)

        for imp in import_symbols:
            source_module = imp.file_path
            raw_text = imp.name.strip()

            # Simple module resolution logic
            target_path = self._resolve_target_module(raw_text, source_module, known_files)

            if target_path in known_files:
                graph.add_edge(
                    Edge(
                        source_id=source_module,
                        target_id=target_path,
                        relation_type=RelationType.IMPORTS,
                        metadata={"internal": True, "raw_import": raw_text},
                    )
                )
            else:
                ext_id = f"external:{raw_text}"
                graph.add_node(
                    Node(id=ext_id, label=raw_text, node_type=NodeType.EXTERNAL)
                )
                graph.add_edge(
                    Edge(
                        source_id=source_module,
                        target_id=ext_id,
                        relation_type=RelationType.IMPORTS,
                        metadata={"internal": False, "raw_import": raw_text},
                    )
                )

        logger.debug(
            "Import graph built: %d nodes, %d edges", len(graph.nodes), len(graph.edges)
        )
        return graph

    def build_dependency_graph(self, import_graph: Graph) -> Graph:
        """Construct a high-level Module Dependency Graph from an import graph.

        Args:
            import_graph: Populated import graph.

        Returns:
            Graph instance summarizing module dependencies.
        """
        dep_graph = Graph(name="dependency_graph")

        for node in import_graph.nodes.values():
            dep_graph.add_node(node)

        for edge in import_graph.edges:
            dep_graph.add_edge(
                Edge(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relation_type=RelationType.DEPENDS_ON,
                    metadata=edge.metadata,
                )
            )

        return dep_graph

    def _resolve_target_module(
        self, import_stmt: str, current_file: str, known_files: Set[str]
    ) -> str:
        """Resolve import statement string to relative file path if internal."""
        cleaned = import_stmt.replace("import ", "").replace("from ", "").strip()
        parts = cleaned.split()
        mod_name = parts[0] if parts else cleaned

        # Convert dot notation to path
        candidate_py = mod_name.replace(".", "/") + ".py"
        if candidate_py in known_files:
            return candidate_py

        candidate_init = mod_name.replace(".", "/") + "/__init__.py"
        if candidate_init in known_files:
            return candidate_init

        # Relative import resolution
        if mod_name.startswith("."):
            current_dir = "/".join(current_file.split("/")[:-1])
            rel_path = (current_dir + "/" + mod_name.lstrip(".")).strip("/") + ".py"
            if rel_path in known_files:
                return rel_path

        return mod_name
