"""Repository Intelligence Foundation.

Master engine orchestrating discovery, parsing, chunking, symbol indexing,
relationship graphs, metrics, static analysis, and security scanning.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.chunking.models import ChunkStats, CodeChunk
from app.chunking.service import ChunkingService
from app.core.logging import setup_logger
from app.graphs.builder import RelationshipEngine
from app.graphs.models import RepositoryGraphs
from app.indexing.index import UnifiedRepositoryIndex
from app.indexing.service import IndexingService
from app.metrics.calculator import MetricsEngine
from app.metrics.models import RepositoryMetrics
from app.parsing.models import ParseResult
from app.parsing.service import ParsingEngine
from app.repository.discovery import RepositoryDiscoveryEngine
from app.repository.models import RepositoryMetadata, RepositoryStats, SourceFile
from app.security.models import SecurityReport
from app.security.registry import SecurityEngine
from app.static_analysis.models import StaticAnalysisReport
from app.static_analysis.registry import StaticAnalysisEngine
from app.symbols.models import Symbol, SymbolStats
from app.symbols.service import SymbolService

logger = setup_logger("repository.intelligence")


@dataclass
class ParsingStats:
    """Aggregated statistics for AST parsing operations."""

    total_files_parsed: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    files_with_syntax_errors: int = 0
    total_parse_duration_ms: float = 0.0
    average_parse_duration_ms: float = 0.0


@dataclass
class RepositoryIntelligenceResult:
    """Complete intelligence analysis result for a target repository across Phases 1–10."""

    metadata: RepositoryMetadata
    source_files: List[SourceFile]
    parse_results: List[ParseResult]
    chunks: List[CodeChunk]
    symbol_index: Any
    unified_index: UnifiedRepositoryIndex
    graphs: RepositoryGraphs
    metrics: RepositoryMetrics
    static_analysis: StaticAnalysisReport
    security: SecurityReport
    repo_stats: RepositoryStats
    parsing_stats: ParsingStats
    chunk_stats: ChunkStats
    symbol_stats: SymbolStats
    summary: Dict[str, Any] = field(default_factory=dict)


class RepositoryIntelligenceEngine:
    """Master engine orchestrating all PRAudit analysis engines (Phases 1–10)."""

    def __init__(
        self,
        discovery_engine: Optional[RepositoryDiscoveryEngine] = None,
        parsing_engine: Optional[ParsingEngine] = None,
        chunking_service: Optional[ChunkingService] = None,
        symbol_service: Optional[SymbolService] = None,
        relationship_engine: Optional[RelationshipEngine] = None,
        indexing_service: Optional[IndexingService] = None,
        metrics_engine: Optional[MetricsEngine] = None,
        static_analysis_engine: Optional[StaticAnalysisEngine] = None,
        security_engine: Optional[SecurityEngine] = None,
    ) -> None:
        """Initialize RepositoryIntelligenceEngine with sub-engines."""
        self.discovery_engine = discovery_engine or RepositoryDiscoveryEngine()
        self.parsing_engine = parsing_engine or ParsingEngine()
        self.chunking_service = chunking_service or ChunkingService()
        self.symbol_service = symbol_service or SymbolService()
        self.relationship_engine = relationship_engine or RelationshipEngine()
        self.indexing_service = indexing_service or IndexingService()
        self.metrics_engine = metrics_engine or MetricsEngine()
        self.static_analysis_engine = static_analysis_engine or StaticAnalysisEngine()
        self.security_engine = security_engine or SecurityEngine()

    def analyze_repository(self, repo_path: Path) -> RepositoryIntelligenceResult:
        """Perform full repository analysis across Phases 1 through 10.

        Args:
            repo_path: Path to target repository directory.

        Returns:
            RepositoryIntelligenceResult holding all analysis artifacts.
        """
        logger.info("Starting complete repository intelligence analysis for %s", repo_path)

        # Phase 1: Discovery
        metadata, source_files, repo_stats = self.discovery_engine.discover(repo_path)

        # Phase 2, 3, 4: Parse, Chunk, Extract Symbols
        parse_results: List[ParseResult] = []
        all_chunks: List[CodeChunk] = []
        all_symbols: List[Symbol] = []

        total_parse_duration = 0.0
        success_parses = 0
        failed_parses = 0
        syntax_error_files = 0

        for sf in source_files:
            if not sf.is_supported:
                continue

            parse_res = self.parsing_engine.parse_file(sf)
            parse_results.append(parse_res)

            total_parse_duration += parse_res.parse_duration_ms
            if parse_res.is_success:
                success_parses += 1
            else:
                failed_parses += 1

            if parse_res.has_syntax_errors:
                syntax_error_files += 1

            chunks = self.chunking_service.extract_chunks_from_file(sf, parse_res)
            all_chunks.extend(chunks)

            symbols = self.symbol_service.extract_symbols_from_file(sf, parse_res)
            all_symbols.extend(symbols)

        # Phase 6: Relationship Graphs
        graphs = self.relationship_engine.build_all_graphs(
            source_files, parse_results, self.symbol_service.index
        )

        # Phase 7: Unified Multi-Indexing
        unified_index = self.indexing_service.build_index(
            source_files, all_symbols, all_chunks
        )

        # Phase 8: Code Quality Metrics
        metrics = self.metrics_engine.analyze_repository_metrics(source_files, parse_results)

        # Phase 9: Static Analysis
        static_report = self.static_analysis_engine.run_analysis(
            metadata.root_path, source_files, parse_results
        )

        # Phase 10: Security Scanning
        security_report = self.security_engine.run_security_scan(
            metadata.root_path, source_files, parse_results
        )

        # Phase 5 & 10 Summary Aggregation
        parsing_stats = ParsingStats(
            total_files_parsed=len(parse_results),
            successful_parses=success_parses,
            failed_parses=failed_parses,
            files_with_syntax_errors=syntax_error_files,
            total_parse_duration_ms=round(total_parse_duration, 2),
            average_parse_duration_ms=(
                round(total_parse_duration / max(1, len(parse_results)), 2)
            ),
        )

        chunk_stats = self.chunking_service.compute_stats(all_chunks)
        symbol_stats = self.symbol_service.compute_stats(all_symbols)
        supported_languages = sorted(list({sf.language.value for sf in source_files if sf.is_supported}))

        summary = {
            "repository_name": metadata.name,
            "root_path": str(metadata.root_path),
            "is_git_repo": metadata.is_git_repository,
            "head_commit": metadata.git_head_commit,
            "total_files": repo_stats.file_stats.total_files,
            "supported_files": repo_stats.file_stats.supported_files,
            "ignored_files": repo_stats.file_stats.ignored_files,
            "total_lines_of_code": repo_stats.file_stats.total_lines,
            "total_bytes": repo_stats.file_stats.total_bytes,
            "supported_languages": supported_languages,
            "total_chunks": chunk_stats.total_chunks,
            "total_symbols": symbol_stats.total_symbols,
            "call_graph_nodes": len(graphs.call_graph.nodes),
            "call_graph_edges": len(graphs.call_graph.edges),
            "import_graph_nodes": len(graphs.import_graph.nodes),
            "average_maintainability_index": metrics.average_maintainability_index,
            "average_cyclomatic_complexity": metrics.average_cyclomatic_complexity,
            "static_analysis_findings_count": static_report.total_findings,
            "security_vulnerabilities_count": security_report.total_vulnerabilities,
        }

        logger.info(
            "Complete repository analysis finished for %s: %d files, %d chunks, %d symbols, %d static findings, %d security findings.",
            metadata.name,
            repo_stats.file_stats.total_files,
            chunk_stats.total_chunks,
            symbol_stats.total_symbols,
            static_report.total_findings,
            security_report.total_vulnerabilities,
        )

        return RepositoryIntelligenceResult(
            metadata=metadata,
            source_files=source_files,
            parse_results=parse_results,
            chunks=all_chunks,
            symbol_index=self.symbol_service.index,
            unified_index=unified_index,
            graphs=graphs,
            metrics=metrics,
            static_analysis=static_report,
            security=security_report,
            repo_stats=repo_stats,
            parsing_stats=parsing_stats,
            chunk_stats=chunk_stats,
            symbol_stats=symbol_stats,
            summary=summary,
        )
