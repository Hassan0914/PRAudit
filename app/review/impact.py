"""Change Impact Engine calculating downstream callers and upstream dependencies."""

from typing import Dict, List, Set, Tuple
from app.core.logging import setup_logger
from app.git.pr_models import PullRequest
from app.graphs.models import RepositoryGraphs
from app.review.impact_models import (
    ImpactAnalysisReport,
    ImpactEdge,
    ImpactLevel,
    ImpactNode,
    ImpactStatistics,
)
from app.symbols.index import SymbolIndex

logger = setup_logger("review.impact")


class ChangeImpactEngine:
    """Engine calculating impact radius of PR code changes across repository graphs."""

    def analyze_impact(
        self,
        pr: PullRequest,
        graphs: RepositoryGraphs,
        symbol_index: SymbolIndex,
        max_depth: int = 3,
    ) -> ImpactAnalysisReport:
        """Perform change impact analysis for a Pull Request.

        Args:
            pr: PullRequest model.
            graphs: RepositoryGraphs container.
            symbol_index: Indexed symbols.
            max_depth: Maximum traversal depth for downstream/upstream graph propagation.

        Returns:
            ImpactAnalysisReport container.
        """
        logger.info("Performing change impact analysis for PR %s (max_depth=%d)", pr.pr_id, max_depth)

        direct_files = [f.file_path for f in pr.files]

        # Identify directly changed symbols
        direct_symbols: Set[str] = set()
        for f in pr.files:
            for hunk in f.hunks:
                for lc in hunk.line_changes:
                    if lc.enclosing_symbol_id:
                        direct_symbols.add(lc.enclosing_symbol_id)

        impact_nodes: Dict[str, ImpactNode] = {}
        impact_edges: List[ImpactEdge] = []

        # Add directly modified file nodes
        for df in direct_files:
            node_id = f"file:{df}"
            impact_nodes[node_id] = ImpactNode(
                id=node_id,
                name=df,
                node_type="file",
                file_path=df,
                impact_level=ImpactLevel.DIRECT,
                depth=0,
            )

        # Add directly modified symbols
        for sym_id in direct_symbols:
            sym = symbol_index.get_by_id(sym_id)
            if sym:
                impact_nodes[sym.symbol_id] = ImpactNode(
                    id=sym.symbol_id,
                    name=sym.name,
                    node_type=sym.kind.value,
                    file_path=sym.file_path,
                    impact_level=ImpactLevel.DIRECT,
                    depth=0,
                )

        # Traverse downstream callers using Call Graph
        downstream_count = self._traverse_call_graph(
            graphs.call_graph, direct_symbols, symbol_index, max_depth, impact_nodes, impact_edges
        )

        # Traverse upstream module dependencies using Import Graph
        upstream_count = self._traverse_import_graph(
            graphs.import_graph, set(direct_files), max_depth, impact_nodes, impact_edges
        )

        impacted_files = sorted(list({node.file_path for node in impact_nodes.values() if node.file_path}))

        funcs_c = sum(1 for n in impact_nodes.values() if n.node_type in {"function", "method"})
        classes_c = sum(1 for n in impact_nodes.values() if n.node_type == "class")
        modules_c = sum(1 for n in impact_nodes.values() if n.node_type in {"module", "file"})

        stats = ImpactStatistics(
            total_affected_entities=len(impact_nodes),
            directly_modified_files=len(direct_files),
            affected_functions_count=funcs_c,
            affected_classes_count=classes_c,
            affected_modules_count=modules_c,
            downstream_callers_count=downstream_count,
            upstream_dependencies_count=upstream_count,
        )

        logger.info(
            "Impact analysis complete: %d total entities affected across %d files.",
            len(impact_nodes),
            len(impacted_files),
        )

        return ImpactAnalysisReport(
            pr_id=pr.pr_id,
            traversal_depth=max_depth,
            direct_modified_files=direct_files,
            affected_nodes=list(impact_nodes.values()),
            impact_edges=impact_edges,
            impacted_files=impacted_files,
            statistics=stats,
        )

    def _traverse_call_graph(
        self,
        call_graph,
        start_symbols: Set[str],
        symbol_index: SymbolIndex,
        max_depth: int,
        impact_nodes: Dict[str, ImpactNode],
        impact_edges: List[ImpactEdge],
    ) -> int:
        """BFS traversal over Call Graph to find downstream callers."""
        queue: List[Tuple[str, int]] = [(s_id, 0) for s_id in start_symbols]
        visited = set(start_symbols)
        count = 0

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Look for callers where caller -> curr_id
            for edge in call_graph.edges:
                if edge.target_id == curr_id and edge.source_id not in visited:
                    caller_id = edge.source_id
                    visited.add(caller_id)
                    count += 1

                    sym = symbol_index.get_by_id(caller_id)
                    file_p = sym.file_path if sym else ""
                    name_str = sym.name if sym else caller_id

                    impact_nodes[caller_id] = ImpactNode(
                        id=caller_id,
                        name=name_str,
                        node_type="function",
                        file_path=file_p,
                        impact_level=ImpactLevel.INDIRECT,
                        depth=depth + 1,
                    )
                    impact_edges.append(
                        ImpactEdge(source_id=caller_id, target_id=curr_id, relationship="calls")
                    )
                    queue.append((caller_id, depth + 1))

        return count

    def _traverse_import_graph(
        self,
        import_graph,
        start_files: Set[str],
        max_depth: int,
        impact_nodes: Dict[str, ImpactNode],
        impact_edges: List[ImpactEdge],
    ) -> int:
        """BFS traversal over Import Graph to find modules importing changed files."""
        queue: List[Tuple[str, int]] = [(f_path, 0) for f_path in start_files]
        visited = set(start_files)
        count = 0

        while queue:
            curr_file, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for edge in import_graph.edges:
                if edge.target_id == curr_file and edge.source_id not in visited:
                    importer_id = edge.source_id
                    visited.add(importer_id)
                    count += 1

                    node_id = f"module:{importer_id}"
                    impact_nodes[node_id] = ImpactNode(
                        id=node_id,
                        name=importer_id,
                        node_type="module",
                        file_path=importer_id,
                        impact_level=ImpactLevel.INDIRECT,
                        depth=depth + 1,
                    )
                    impact_edges.append(
                        ImpactEdge(source_id=importer_id, target_id=curr_file, relationship="imports")
                    )
                    queue.append((importer_id, depth + 1))

        return count
