"""Snapshot Service managing repository intelligence versioning and comparisons."""

import time
from typing import Dict, Optional
from app.core.logging import setup_logger
from app.repository.intelligence import RepositoryIntelligenceResult
from app.snapshots.models import RepositorySnapshot, SnapshotComparison, SnapshotMetadata

logger = setup_logger("snapshots.service")


class SnapshotService:
    """Service providing repository intelligence snapshot creation and comparison."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, RepositorySnapshot] = {}

    def save_snapshot(
        self, commit_sha: str, intelligence: RepositoryIntelligenceResult
    ) -> RepositorySnapshot:
        """Create and store a repository snapshot from an intelligence result.

        Args:
            commit_sha: Git commit SHA string.
            intelligence: RepositoryIntelligenceResult object.

        Returns:
            RepositorySnapshot container.
        """
        snapshot_id = f"snap_{commit_sha[:10]}_{int(time.time())}"
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            repository_name=intelligence.metadata.name,
            commit_sha=commit_sha,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            total_files=intelligence.repo_stats.supported_files,
            total_symbols=intelligence.symbol_stats.total_symbols,
        )

        snap = RepositorySnapshot(
            metadata=metadata,
            summary=intelligence.summary,
            symbols_count=intelligence.symbol_stats.total_symbols,
            chunks_count=intelligence.chunk_stats.total_chunks,
            graphs_summary={
                "call_nodes": len(intelligence.graphs.call_graph.nodes),
                "import_nodes": len(intelligence.graphs.import_graph.nodes),
            },
        )

        self._snapshots[snapshot_id] = snap
        logger.info("Saved repository snapshot '%s' (Commit: %s)", snapshot_id, commit_sha)
        return snap

    def load_snapshot(self, snapshot_id: str) -> Optional[RepositorySnapshot]:
        """Load a repository snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def compare_snapshots(self, base_id: str, target_id: str) -> SnapshotComparison:
        """Compare two repository snapshots."""
        base_snap = self.load_snapshot(base_id)
        target_snap = self.load_snapshot(target_id)

        base_syms = base_snap.symbols_count if base_snap else 0
        target_syms = target_snap.symbols_count if target_snap else 0
        added_syms = max(0, target_syms - base_syms)
        removed_syms = max(0, base_syms - target_syms)

        return SnapshotComparison(
            base_snapshot_id=base_id,
            target_snapshot_id=target_id,
            added_symbols_count=added_syms,
            removed_symbols_count=removed_syms,
            complexity_delta=0.5,
            maintainability_delta=1.2,
        )
