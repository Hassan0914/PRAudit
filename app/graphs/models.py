"""Data models for repository relationship graphs and network representations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class NodeType(str, Enum):
    """Types of graph nodes."""

    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    FILE = "file"
    EXTERNAL = "external"


class RelationType(str, Enum):
    """Types of graph edges/relationships."""

    CALLS = "calls"
    INHERITS = "inherits"
    IMPORTS = "imports"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"


@dataclass
class Node:
    """Represents a vertex in a repository graph."""

    id: str
    label: str
    node_type: NodeType
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """Represents a directed edge in a repository graph."""

    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphStats:
    """Statistics describing graph topology."""

    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    has_cycles: bool = False
    max_depth: int = 0


class Graph:
    """Strongly typed directed graph data structure."""

    def __init__(self, name: str = "graph") -> None:
        """Initialize empty Graph.

        Args:
            name: Label or type name for the graph.
        """
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, Set[str]] = {}
        self._in_degree: Dict[str, int] = {}
        self._out_degree: Dict[str, int] = {}

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: Node instance.
        """
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self._adjacency[node.id] = set()
            self._in_degree[node.id] = 0
            self._out_degree[node.id] = 0

    def add_edge(self, edge: Edge) -> None:
        """Add a directed edge to the graph.

        Args:
            edge: Edge instance.
        """
        if edge.source_id not in self.nodes:
            self.add_node(
                Node(id=edge.source_id, label=edge.source_id, node_type=NodeType.EXTERNAL)
            )
        if edge.target_id not in self.nodes:
            self.add_node(
                Node(id=edge.target_id, label=edge.target_id, node_type=NodeType.EXTERNAL)
            )

        self.edges.append(edge)
        self._adjacency[edge.source_id].add(edge.target_id)
        self._out_degree[edge.source_id] = self._out_degree.get(edge.source_id, 0) + 1
        self._in_degree[edge.target_id] = self._in_degree.get(edge.target_id, 0) + 1

    def get_neighbors(self, node_id: str) -> List[Node]:
        """Get outgoing neighbor nodes for a given node.

        Args:
            node_id: Source node ID.

        Returns:
            List of neighbor Node objects.
        """
        target_ids = self._adjacency.get(node_id, set())
        return [self.nodes[tid] for tid in target_ids if tid in self.nodes]

    def has_cycles(self) -> bool:
        """Detect if the directed graph contains cycles (DFS coloring).

        Returns:
            True if cycles exist, False otherwise.
        """
        visited = set()
        rec_stack = set()

        def _dfs(v: str) -> bool:
            visited.add(v)
            rec_stack.add(v)

            for neighbor in self._adjacency.get(v, set()):
                if neighbor not in visited:
                    if _dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(v)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if _dfs(node_id):
                    return True
        return False

    def compute_stats(self) -> GraphStats:
        """Compute structural statistics for the graph.

        Returns:
            GraphStats model.
        """
        n = len(self.nodes)
        e = len(self.edges)
        density = round(e / (n * (n - 1)), 4) if n > 1 else 0.0
        return GraphStats(
            node_count=n,
            edge_count=e,
            density=density,
            has_cycles=self.has_cycles(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph into a dictionary representation.

        Returns:
            Serializable dictionary.
        """
        return {
            "name": self.name,
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.node_type.value,
                    "file_path": n.file_path,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation_type.value,
                }
                for e in self.edges
            ],
            "stats": self.compute_stats().__dict__,
        }


@dataclass
class RepositoryGraphs:
    """Container holding all relationship graphs for a repository."""

    call_graph: Graph = field(default_factory=lambda: Graph("call_graph"))
    import_graph: Graph = field(default_factory=lambda: Graph("import_graph"))
    dependency_graph: Graph = field(default_factory=lambda: Graph("dependency_graph"))
    inheritance_graph: Graph = field(default_factory=lambda: Graph("inheritance_graph"))
