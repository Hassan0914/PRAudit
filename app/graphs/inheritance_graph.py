"""Class Inheritance Graph builder."""

from typing import List
import tree_sitter

from app.core.logging import setup_logger
from app.graphs.models import Edge, Graph, Node, NodeType, RelationType
from app.parsing.models import ParseResult
from app.symbols.index import SymbolIndex
from app.symbols.models import SymbolKind

logger = setup_logger("graphs.inheritance_graph")


class InheritanceGraphBuilder:
    """Builder for constructing class inheritance graphs."""

    def build_inheritance_graph(
        self, parse_results: List[ParseResult], symbol_index: SymbolIndex
    ) -> Graph:
        """Construct a Class Inheritance Graph mapping subclass -> superclass relations.

        Args:
            parse_results: List of AST parse results.
            symbol_index: Indexed symbols.

        Returns:
            Graph instance for class inheritance.
        """
        graph = Graph(name="inheritance_graph")

        class_symbols = symbol_index.lookup_by_kind(SymbolKind.CLASS)
        for cls in class_symbols:
            graph.add_node(
                Node(
                    id=cls.symbol_id,
                    label=cls.name,
                    node_type=NodeType.CLASS,
                    file_path=cls.file_path,
                )
            )

        for pr in parse_results:
            if not pr.raw_tree or not pr.raw_tree.root_node:
                continue

            self._extract_inheritance(pr.raw_tree.root_node, pr.file_path, symbol_index, graph)

        logger.debug(
            "Inheritance graph built: %d nodes, %d edges", len(graph.nodes), len(graph.edges)
        )
        return graph

    def _extract_inheritance(
        self,
        root_node: tree_sitter.Node,
        file_path: str,
        symbol_index: SymbolIndex,
        graph: Graph,
    ) -> None:
        """Traverse AST to extract superclasses."""

        def _traverse(node: tree_sitter.Node) -> None:
            if node.type in {"class_definition", "class_declaration"}:
                class_name = None
                superclasses: List[str] = []

                for child in node.children:
                    if child.type == "identifier":
                        class_name = child.text.decode("utf-8", errors="ignore")
                    elif child.type == "argument_list":  # Python inheritance
                        for arg in child.children:
                            if arg.type == "identifier":
                                superclasses.append(arg.text.decode("utf-8", errors="ignore"))
                    elif child.type == "class_heritage":  # JS/TS extends
                        for heritage in child.children:
                            if heritage.type == "identifier":
                                superclasses.append(heritage.text.decode("utf-8", errors="ignore"))

                if class_name:
                    sub_matches = symbol_index.lookup_by_name(class_name)
                    if sub_matches:
                        sub_id = sub_matches[0].symbol_id
                        for super_name in superclasses:
                            super_matches = symbol_index.lookup_by_name(super_name)
                            if super_matches:
                                super_id = super_matches[0].symbol_id
                                graph.add_edge(
                                    Edge(
                                        source_id=sub_id,
                                        target_id=super_id,
                                        relation_type=RelationType.INHERITS,
                                    )
                                )
                            else:
                                ext_id = f"ext_class:{super_name}"
                                graph.add_node(
                                    Node(id=ext_id, label=super_name, node_type=NodeType.EXTERNAL)
                                )
                                graph.add_edge(
                                    Edge(
                                        source_id=sub_id,
                                        target_id=ext_id,
                                        relation_type=RelationType.INHERITS,
                                    )
                                )

            for child in node.children:
                _traverse(child)

        _traverse(root_node)
