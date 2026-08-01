"""Unit tests for Phase 25: Repository Snapshot Engine."""

from pathlib import Path
from app.repository.intelligence import RepositoryIntelligenceEngine
from app.snapshots.service import SnapshotService


def test_snapshot_service(temp_repo: Path) -> None:
    intel_engine = RepositoryIntelligenceEngine()
    intel = intel_engine.analyze_repository(temp_repo)

    service = SnapshotService()
    snap1 = service.save_snapshot("commit_sha_1", intel)
    assert snap1.metadata.snapshot_id is not None

    snap2 = service.save_snapshot("commit_sha_2", intel)

    comp = service.compare_snapshots(snap1.metadata.snapshot_id, snap2.metadata.snapshot_id)
    assert comp.base_snapshot_id == snap1.metadata.snapshot_id
    assert comp.target_snapshot_id == snap2.metadata.snapshot_id
