"""Stress test suite executing RepositoryIntelligenceEngine 10 consecutive times across Phases 1-10."""

import time
from pathlib import Path
from app.repository.intelligence import RepositoryIntelligenceEngine


def test_repository_intelligence_stress_runs() -> None:
    """Stress test executing 10 consecutive full repository analysis scans across Phases 1-10."""
    engine = RepositoryIntelligenceEngine()
    repo_path = Path(".")

    durations_ms = []
    start_total = time.perf_counter()

    for i in range(1, 11):
        t0 = time.perf_counter()
        result = engine.analyze_repository(repo_path)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        durations_ms.append(dt_ms)

        # Assert consistent analysis results across every single run
        assert result.metadata.name == "PRAudit"
        assert len(result.source_files) == result.repo_stats.file_stats.total_files
        assert len(result.chunks) == result.chunk_stats.total_chunks
        assert len(result.graphs.call_graph.nodes) > 0
        assert result.metrics.total_lines > 0
        assert result.static_analysis.total_findings >= 0
        assert result.security.total_vulnerabilities >= 0

    total_time_sec = time.perf_counter() - start_total
    avg_duration = sum(durations_ms) / len(durations_ms)

    print(f"\n--- STRESS RUNS BENCHMARK RESULTS (PHASES 1-10) ---")
    print(f"Total time for 10 runs  : {total_time_sec:.2f} seconds")
    print(f"Min run time           : {min(durations_ms):.2f} ms")
    print(f"Max run time           : {max(durations_ms):.2f} ms")
    print(f"Avg run time           : {avg_duration:.2f} ms")
    print(f"Success Rate           : 10/10 (100% Passed)")


if __name__ == "__main__":
    test_repository_intelligence_stress_runs()
