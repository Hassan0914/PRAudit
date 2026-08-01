"""Chunking Service for extracting semantic code chunks across source files."""

from typing import List, Tuple
from app.core.exceptions import ChunkExtractionError
from app.core.logging import setup_logger
from app.core.types import ChunkType, Language
from app.chunking.extractor import ChunkExtractorFactory
from app.chunking.models import ChunkStats, CodeChunk
from app.parsing.models import ParseResult
from app.repository.models import SourceFile

logger = setup_logger("chunking.service")


class ChunkingService:
    """Service responsible for semantic code chunk extraction and statistics aggregation."""

    def extract_chunks_from_parse(
        self, parse_result: ParseResult, source_code: str
    ) -> List[CodeChunk]:
        """Extract semantic code chunks from a ParseResult and source code text.

        Args:
            parse_result: AST ParseResult object.
            source_code: Source code text string.

        Returns:
            List of extracted CodeChunk objects.
        """
        if not source_code or not source_code.strip():
            return []

        try:
            extractor = ChunkExtractorFactory.get_extractor(parse_result.language)
            chunks = extractor.extract_chunks(parse_result, source_code)
            logger.debug(
                "Extracted %d chunks for file %s (language: %s)",
                len(chunks),
                parse_result.file_path,
                parse_result.language.value,
            )
            return chunks
        except Exception as exc:
            logger.error(
                "Error extracting chunks for file %s: %s", parse_result.file_path, exc, exc_info=True
            )
            raise ChunkExtractionError(
                f"Failed to extract semantic chunks for file '{parse_result.file_path}': {exc}"
            ) from exc

    def extract_chunks_from_file(
        self, source_file: SourceFile, parse_result: ParseResult
    ) -> List[CodeChunk]:
        """Extract semantic chunks from a SourceFile.

        Args:
            source_file: SourceFile domain model.
            parse_result: Output from ParsingEngine.

        Returns:
            List of CodeChunk instances.
        """
        try:
            source_code = source_file.absolute_path.read_text(encoding="utf-8", errors="ignore")
            return self.extract_chunks_from_parse(parse_result, source_code)
        except Exception as exc:
            logger.warning(
                "Could not read source code for file %s during chunking: %s",
                source_file.relative_path,
                exc,
            )
            return []

    def compute_stats(self, chunks: List[CodeChunk]) -> ChunkStats:
        """Compute aggregate statistics for a collection of CodeChunk objects.

        Args:
            chunks: List of CodeChunk objects.

        Returns:
            Aggregated ChunkStats instance.
        """
        stats = ChunkStats(total_chunks=len(chunks))
        if not chunks:
            return stats

        total_lines = 0
        for chunk in chunks:
            line_count = (chunk.end_line - chunk.start_line) + 1
            total_lines += line_count

            if chunk.chunk_type == ChunkType.FUNCTION:
                stats.function_count += 1
            elif chunk.chunk_type == ChunkType.CLASS:
                stats.class_count += 1
            elif chunk.chunk_type == ChunkType.METHOD:
                stats.method_count += 1
            elif chunk.chunk_type == ChunkType.MODULE:
                stats.module_count += 1
            elif chunk.chunk_type == ChunkType.BLOCK:
                stats.block_count += 1

        stats.average_lines_per_chunk = round(total_lines / len(chunks), 2)
        return stats
