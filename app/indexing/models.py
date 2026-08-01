"""Data models for repository multi-indexing and prefix search."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.chunking.models import CodeChunk
from app.core.types import Language, SymbolKind
from app.repository.models import SourceFile
from app.symbols.models import Symbol


@dataclass
class IndexSearchResult:
    """Container holding matching entities from index queries."""

    query: str
    files: List[SourceFile] = field(default_factory=list)
    symbols: List[Symbol] = field(default_factory=list)
    chunks: List[CodeChunk] = field(default_factory=list)
    total_matches: int = 0


@dataclass
class IndexStats:
    """Statistics detailing indexed repository entities."""

    indexed_files_count: int = 0
    indexed_symbols_count: int = 0
    indexed_chunks_count: int = 0
    indexed_imports_count: int = 0
