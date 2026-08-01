"""Incremental Analysis Engine performing selective delta updates from Git diffs."""

from typing import List, Set
from app.core.logging import setup_logger
from app.git.pr_models import PullRequest
from app.incremental.models import (
    AffectedChunk,
    AffectedSymbol,
    ChangedArtifact,
    IncrementalDeltaReport,
)
from app.repository.intelligence import RepositoryIntelligenceResult

logger = setup_logger("incremental.service")


class IncrementalAnalysisEngine:
    """Engine analyzing PR diffs to perform targeted incremental updates."""

    def analyze_delta(
        self, pr: PullRequest, intelligence: RepositoryIntelligenceResult
    ) -> IncrementalDeltaReport:
        """Analyze PR diff and identify affected symbols, chunks, and files.

        Args:
            pr: PullRequest model.
            intelligence: RepositoryIntelligenceResult model.

        Returns:
            IncrementalDeltaReport container.
        """
        logger.info("Performing incremental delta analysis for PR %s", pr.pr_id)

        changed_files = [f.file_path for f in pr.files]
        affected_symbols: List[AffectedSymbol] = []
        affected_chunks: List[AffectedChunk] = []

        for pr_file in pr.files:
            file_syms = intelligence.symbol_index.lookup_by_file(pr_file.file_path)
            for sym in file_syms:
                affected_symbols.append(
                    AffectedSymbol(
                        symbol_id=sym.symbol_id,
                        name=sym.name,
                        file_path=sym.file_path,
                        propagation_reason="DIRECT",
                    )
                )

            # Check impacted chunks
            chunks = intelligence.chunks
            for ch in chunks:
                if ch.file_path == pr_file.file_path:
                    affected_chunks.append(
                        AffectedChunk(
                            chunk_id=ch.chunk_id,
                            file_path=ch.file_path,
                            start_line=ch.start_line,
                            end_line=ch.end_line,
                        )
                    )

        logger.info(
            "Incremental analysis complete: %d affected symbols, %d affected chunks across %d files.",
            len(affected_symbols),
            len(affected_chunks),
            len(changed_files),
        )

        return IncrementalDeltaReport(
            pr_id=pr.pr_id,
            changed_files_count=len(changed_files),
            affected_symbols=affected_symbols,
            affected_chunks=affected_chunks,
            reanalyzed_files=changed_files,
        )
