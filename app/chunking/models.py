"""Data models for semantic code chunks and chunking statistics."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.core.types import ChunkType, Language


@dataclass
class ChunkMetadata:
    """Metadata describing details of a semantic chunk."""

    node_type: str
    parent_symbol: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeChunk:
    """Represents a discrete semantic chunk of source code (function, class, method)."""

    chunk_id: str
    file_path: str
    language: Language
    chunk_type: ChunkType
    symbol_name: str
    source_code: str
    start_line: int
    end_line: int
    parent_chunk_id: Optional[str] = None
    metadata: ChunkMetadata = field(default_factory=lambda: ChunkMetadata(node_type="unknown"))


@dataclass
class ChunkStats:
    """Statistics summarizing extracted semantic chunks."""

    total_chunks: int = 0
    function_count: int = 0
    class_count: int = 0
    method_count: int = 0
    module_count: int = 0
    block_count: int = 0
    average_lines_per_chunk: float = 0.0
