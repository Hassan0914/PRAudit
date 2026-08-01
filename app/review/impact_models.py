"""Data models for change impact analysis and propagation graphs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class ImpactLevel(str, Enum):
    """Level of impact on a repository entity."""

    DIRECT = "DIRECT"        # Directly modified in the PR diff
    INDIRECT = "INDIRECT"    # Affected via call or dependency propagation


@dataclass
class ImpactNode:
    """Represents a node in the impact propagation graph."""

    id: str
    name: str
    node_type: str
    file_path: str
    impact_level: ImpactLevel
    depth: int = 0


@dataclass
class ImpactEdge:
    """Represents a propagation link between impact nodes."""

    source_id: str
    target_id: str
    relationship: str


@dataclass
class ImpactStatistics:
    """Aggregate statistics for change impact analysis."""

    total_affected_entities: int = 0
    directly_modified_files: int = 0
    affected_functions_count: int = 0
    affected_classes_count: int = 0
    affected_modules_count: int = 0
    downstream_callers_count: int = 0
    upstream_dependencies_count: int = 0


@dataclass
class ImpactAnalysisReport:
    """Report detailing downstream and upstream change impacts for a PR."""

    pr_id: str
    traversal_depth: int
    direct_modified_files: List[str] = field(default_factory=list)
    affected_nodes: List[ImpactNode] = field(default_factory=list)
    impact_edges: List[ImpactEdge] = field(default_factory=list)
    impacted_files: List[str] = field(default_factory=list)
    statistics: ImpactStatistics = field(default_factory=ImpactStatistics)
