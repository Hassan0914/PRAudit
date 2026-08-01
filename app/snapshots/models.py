"""Data models for repository intelligence snapshots and snapshot diffing."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SnapshotMetadata:
    """Metadata describing a saved repository snapshot."""

    snapshot_id: str
    repository_name: str
    commit_sha: str
    created_at: str = ""
    total_files: int = 0
    total_symbols: int = 0


@dataclass
class RepositorySnapshot:
    """Saved snapshot container storing full repository state."""

    metadata: SnapshotMetadata
    summary: Dict[str, Any] = field(default_factory=dict)
    symbols_count: int = 0
    chunks_count: int = 0
    graphs_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SnapshotComparison:
    """Comparison report between two repository snapshots."""

    base_snapshot_id: str
    target_snapshot_id: str
    added_symbols_count: int = 0
    removed_symbols_count: int = 0
    complexity_delta: float = 0.0
    maintainability_delta: float = 0.0
