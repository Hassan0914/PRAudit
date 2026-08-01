"""Indexing service providing repository multi-indexing APIs."""

from typing import List, Optional
from app.chunking.models import CodeChunk
from app.core.logging import setup_logger
from app.indexing.index import UnifiedRepositoryIndex
from app.indexing.models import IndexSearchResult, IndexStats
from app.repository.models import SourceFile
from app.symbols.models import Symbol

logger = setup_logger("indexing.service")


class IndexingService:
    """Service orchestrating building and querying the UnifiedRepositoryIndex."""

    def __init__(self, index: Optional[UnifiedRepositoryIndex] = None) -> None:
        """Initialize IndexingService.

        Args:
            index: Optional existing UnifiedRepositoryIndex.
        """
        self.index = index or UnifiedRepositoryIndex()

    def build_index(
        self,
        source_files: List[SourceFile],
        symbols: List[Symbol],
        chunks: List[CodeChunk],
    ) -> UnifiedRepositoryIndex:
        """Populate the multi-index with files, symbols, and chunks.

        Args:
            source_files: Discovered source files.
            symbols: Extracted repository symbols.
            chunks: Extracted semantic chunks.

        Returns:
            Populated UnifiedRepositoryIndex instance.
        """
        logger.info("Building UnifiedRepositoryIndex...")
        self.index.index_source_files(source_files)
        self.index.index_symbols(symbols)
        self.index.index_chunks(chunks)

        stats = self.index.compute_stats()
        logger.info(
            "UnifiedRepositoryIndex built: %d files, %d symbols, %d chunks indexed.",
            stats.indexed_files_count,
            stats.indexed_symbols_count,
            stats.indexed_chunks_count,
        )
        return self.index

    def search(self, query: str, limit: int = 50) -> IndexSearchResult:
        """Perform prefix/exact search across indexed entities.

        Args:
            query: Query string.
            limit: Maximum result count per category.

        Returns:
            IndexSearchResult container.
        """
        return self.index.prefix_search(query, limit=limit)
