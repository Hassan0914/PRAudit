"""UnifiedRepositoryIndex providing high-performance multi-index lookups and prefix search."""

import threading
from typing import Dict, List, Optional, Set
from app.chunking.models import CodeChunk
from app.core.logging import setup_logger
from app.core.types import Language, SymbolKind
from app.indexing.models import IndexSearchResult, IndexStats
from app.repository.models import SourceFile
from app.symbols.models import Symbol

logger = setup_logger("indexing.index")


class UnifiedRepositoryIndex:
    """Centralized high-performance multi-index for files, symbols, chunks, and imports."""

    def __init__(self) -> None:
        """Initialize empty index structures and thread lock."""
        self._lock = threading.Lock()

        # File Indexes
        self._files_by_path: Dict[str, SourceFile] = {}
        self._files_by_language: Dict[Language, List[SourceFile]] = {}

        # Symbol Indexes
        self._symbols_by_id: Dict[str, Symbol] = {}
        self._symbols_by_name: Dict[str, List[Symbol]] = {}
        self._symbols_by_file: Dict[str, List[Symbol]] = {}
        self._symbols_by_kind: Dict[SymbolKind, List[Symbol]] = {}

        # Chunk Indexes
        self._chunks_by_id: Dict[str, CodeChunk] = {}
        self._chunks_by_symbol: Dict[str, List[CodeChunk]] = {}
        self._chunks_by_file: Dict[str, List[CodeChunk]] = {}

        # Prefix Lookup map: lower_name -> set of (category, id/name)
        self._prefix_map: Dict[str, Set[str]] = {}

    def index_source_files(self, files: List[SourceFile]) -> None:
        """Index a collection of SourceFile models.

        Args:
            files: List of SourceFile objects.
        """
        with self._lock:
            for sf in files:
                self._files_by_path[sf.relative_path] = sf
                self._files_by_language.setdefault(sf.language, []).append(sf)
                self._add_prefix(sf.relative_path.lower(), sf.relative_path)

    def index_symbols(self, symbols: List[Symbol]) -> None:
        """Index a collection of Symbol objects.

        Args:
            symbols: List of Symbol objects.
        """
        with self._lock:
            for sym in symbols:
                self._symbols_by_id[sym.symbol_id] = sym
                self._symbols_by_name.setdefault(sym.name, []).append(sym)
                self._symbols_by_file.setdefault(sym.file_path, []).append(sym)
                self._symbols_by_kind.setdefault(sym.kind, []).append(sym)
                self._add_prefix(sym.name.lower(), sym.name)

    def index_chunks(self, chunks: List[CodeChunk]) -> None:
        """Index a collection of CodeChunk objects.

        Args:
            chunks: List of CodeChunk objects.
        """
        with self._lock:
            for ch in chunks:
                self._chunks_by_id[ch.chunk_id] = ch
                self._chunks_by_symbol.setdefault(ch.symbol_name, []).append(ch)
                self._chunks_by_file.setdefault(ch.file_path, []).append(ch)

    def get_file_by_path(self, relative_path: str) -> Optional[SourceFile]:
        """Lookup source file by relative path."""
        with self._lock:
            return self._files_by_path.get(relative_path)

    def get_files_by_language(self, language: Language) -> List[SourceFile]:
        """Lookup source files by language."""
        with self._lock:
            return list(self._files_by_language.get(language, []))

    def get_symbol_by_id(self, symbol_id: str) -> Optional[Symbol]:
        """Lookup symbol by ID."""
        with self._lock:
            return self._symbols_by_id.get(symbol_id)

    def get_symbols_by_name(self, name: str) -> List[Symbol]:
        """Lookup symbols by exact name."""
        with self._lock:
            return list(self._symbols_by_name.get(name, []))

    def get_symbols_by_file(self, file_path: str) -> List[Symbol]:
        """Lookup symbols defined in a file."""
        with self._lock:
            return list(self._symbols_by_file.get(file_path, []))

    def get_symbols_by_kind(self, kind: SymbolKind) -> List[Symbol]:
        """Lookup symbols by symbol kind."""
        with self._lock:
            return list(self._symbols_by_kind.get(kind, []))

    def get_chunk_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """Lookup chunk by ID."""
        with self._lock:
            return self._chunks_by_id.get(chunk_id)

    def get_chunks_by_file(self, file_path: str) -> List[CodeChunk]:
        """Lookup chunks by file path."""
        with self._lock:
            return list(self._chunks_by_file.get(file_path, []))

    def prefix_search(self, query: str, limit: int = 50) -> IndexSearchResult:
        """Perform prefix search across files, symbols, and chunks.

        Args:
            query: Target search prefix.
            limit: Maximum number of matches to return per category.

        Returns:
            IndexSearchResult containing matching files, symbols, and chunks.
        """
        q_lower = query.lower().strip()
        matched_files: List[SourceFile] = []
        matched_symbols: List[Symbol] = []
        matched_chunks: List[CodeChunk] = []

        if not q_lower:
            return IndexSearchResult(query=query)

        with self._lock:
            # Match files
            for rel_path, sf in self._files_by_path.items():
                if rel_path.lower().startswith(q_lower) or Path_basename_matches(rel_path, q_lower):
                    matched_files.append(sf)
                    if len(matched_files) >= limit:
                        break

            # Match symbols
            for name, syms in self._symbols_by_name.items():
                if name.lower().startswith(q_lower):
                    matched_symbols.extend(syms)
                    if len(matched_symbols) >= limit:
                        break

            # Match chunks
            for sym_name, chs in self._chunks_by_symbol.items():
                if sym_name.lower().startswith(q_lower):
                    matched_chunks.extend(chs)
                    if len(matched_chunks) >= limit:
                        break

        total = len(matched_files) + len(matched_symbols) + len(matched_chunks)
        return IndexSearchResult(
            query=query,
            files=matched_files[:limit],
            symbols=matched_symbols[:limit],
            chunks=matched_chunks[:limit],
            total_matches=total,
        )

    def _add_prefix(self, key_lower: str, val: str) -> None:
        """Add key into prefix map."""
        prefix = ""
        for char in key_lower:
            prefix += char
            self._prefix_map.setdefault(prefix, set()).add(val)

    def compute_stats(self) -> IndexStats:
        """Compute aggregate index statistics.

        Returns:
            IndexStats model.
        """
        with self._lock:
            return IndexStats(
                indexed_files_count=len(self._files_by_path),
                indexed_symbols_count=len(self._symbols_by_id),
                indexed_chunks_count=len(self._chunks_by_id),
                indexed_imports_count=len(self._symbols_by_kind.get(SymbolKind.IMPORT, [])),
            )


def Path_basename_matches(path_str: str, query: str) -> bool:
    """Helper checking if file basename starts with query."""
    parts = path_str.split("/")
    basename = parts[-1] if parts else path_str
    return basename.lower().startswith(query)
