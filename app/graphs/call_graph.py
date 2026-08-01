"""Call Graph builder inspecting AST function invocation nodes."""

from typing import List, Optional
import tree_sitter

from app.core.logging import setup_logger
from app.graphs.models import Edge, Graph, Node, NodeType, RelationType
from app.parsing.models import ParseResult
from app.symbols.index import SymbolIndex
from app.symbols.models import Symbol

logger = setup_logger("graphs.call_graph")


class CallGraphBuilder:
    """Builder for constructing function call graphs."""

    def build_call_graph(
        self, parse_results: List[ParseResult], symbol_index: SymbolIndex
    ) -> Graph:
        """Construct a Call Graph mapping function callers to callees.

        Args:
            parse_results: List of AST parse results.
            symbol_index: Indexed symbols for caller/callee resolution.

        Returns:
            Graph instance containing call relationships.
        """
        graph = Graph(name="call_graph")

        # Add all function & method symbols as nodes
        all_symbols = symbol_index.get_all_symbols()
        for sym in all_symbols:
            if sym.kind.value in {"function", "method"}:
                graph.add_node(
                    Node(
                        id=sym.symbol_id,
                        label=f"{sym.scope_path or sym.name}",
                        node_type=NodeType.FUNCTION,
                        file_path=sym.file_path,
                    )
                )

        for pr in parse_results:
            if not pr.raw_tree or not pr.raw_tree.root_node:
                continue

            file_symbols = symbol_index.lookup_by_file(pr.file_path)
            self._extract_calls(pr.raw_tree.root_node, pr.file_path, file_symbols, symbol_index, graph)

        logger.debug(
            "Call graph built: %d nodes, %d edges", len(graph.nodes), len(graph.edges)
        )
        return graph

    def _extract_calls(
        self,
        root_node: tree_sitter.Node,
        file_path: str,
        file_symbols: List[Symbol],
        symbol_index: SymbolIndex,
        graph: Graph,
    ) -> None:
        """Traverse AST to identify call expressions."""

        def _get_enclosing_function(n: tree_sitter.Node) -> Optional[Symbol]:
            curr = n.parent
            while curr:
                if curr.type in {"function_definition", "function_declaration", "method_definition"}:
                    start_line = curr.start_point[0] + 1
                    for s in file_symbols:
                        if s.location.start_line <= start_line <= s.location.end_line:
                            return s
                curr = curr.parent
            return None

        def _traverse(node: tree_sitter.Node) -> None:
            if node.type in {"call", "call_expression"}:
                caller_sym = _get_enclosing_function(node)
                if caller_sym:
                    # Find called function identifier
                    callee_name = None
                    first_child = node.children[0] if node.children else None
                    if first_child:
                        if first_child.type in {"identifier", "property_identifier"}:
                            callee_name = first_child.text.decode("utf-8", errors="ignore")
                        elif first_child.type == "attribute":
                            # e.g., obj.method()
                            for child in reversed(first_child.children):
                                if child.type == "identifier":
                                    callee_name = child.text.decode("utf-8", errors="ignore")
                                    break

                    if callee_name:
                        matched = symbol_index.lookup_by_name(callee_name)
                        if matched:
                            callee_sym = matched[0]
                            graph.add_edge(
                                Edge(
                                    source_id=caller_sym.symbol_id,
                                    target_id=callee_sym.symbol_id,
                                    relation_type=RelationType.CALLS,
                                )
                            )
                        else:
                            # External or un-indexed call
                            ext_id = f"ext:{callee_name}"
                            graph.add_node(
                                Node(id=ext_id, label=callee_name, node_type=NodeType.EXTERNAL)
                            )
                            graph.add_edge(
                                Edge(
                                    source_id=caller_sym.symbol_id,
                                    target_id=ext_id,
                                    relation_type=RelationType.CALLS,
                                )
                            )

            for child in node.children:
                _traverse(child)

        _traverse(root_node)
