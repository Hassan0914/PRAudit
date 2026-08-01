"""Data models representing repository programming symbols and index statistics."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.core.types import Language, SymbolKind


@dataclass
class SymbolLocation:
    """Location information for a symbol in a source file."""

    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int


@dataclass
class Symbol:
    """Represents a code symbol (function, class, method, import, variable, constant, module)."""

    symbol_id: str
    name: str
    kind: SymbolKind
    file_path: str
    language: Language
    location: SymbolLocation
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_symbol_id: Optional[str] = None
    scope_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SymbolStats:
    """Statistics detailing extracted repository symbols."""

    total_symbols: int = 0
    function_count: int = 0
    class_count: int = 0
    method_count: int = 0
    import_count: int = 0
    export_count: int = 0
    variable_count: int = 0
    constant_count: int = 0
    module_count: int = 0
