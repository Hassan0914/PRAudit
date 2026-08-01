"""In-memory symbol index providing fast querying, indexing, and hierarchy traversal."""

import threading
from typing import Dict, List, Optional
from app.core.logging import setup_logger
from app.core.types import SymbolKind
from app.symbols.models import Symbol

logger = setup_logger("symbols.index")


class SymbolIndex:
    """Indexed storage providing O(1) lookup operations and hierarchy navigation."""

    def __init__(self) -> None:
        """Initialize empty symbol index and threading lock."""
        self._lock = threading.Lock()
        self._symbols_by_id: Dict[str, Symbol] = {}
        self._symbols_by_name: Dict[str, List[Symbol]] = {}
        self._symbols_by_file: Dict[str, List[Symbol]] = {}
        self._symbols_by_kind: Dict[SymbolKind, List[Symbol]] = {}
        self._children_by_parent: Dict[str, List[Symbol]] = {}

    def add_symbol(self, symbol: Symbol) -> None:
        """Add a single symbol to the index.

        Args:
            symbol: Symbol object to index.
        """
        with self._lock:
            self._symbols_by_id[symbol.symbol_id] = symbol

            self._symbols_by_name.setdefault(symbol.name, []).append(symbol)
            self._symbols_by_file.setdefault(symbol.file_path, []).append(symbol)
            self._symbols_by_kind.setdefault(symbol.kind, []).append(symbol)

            if symbol.parent_symbol_id:
                self._children_by_parent.setdefault(symbol.parent_symbol_id, []).append(symbol)

    def add_symbols(self, symbols: List[Symbol]) -> None:
        """Bulk add a list of symbols to the index.

        Args:
            symbols: List of Symbol objects.
        """
        for sym in symbols:
            self.add_symbol(sym)

    def get_by_id(self, symbol_id: str) -> Optional[Symbol]:
        """Retrieve a symbol by its unique ID.

        Args:
            symbol_id: Target symbol identifier string.

        Returns:
            Symbol instance if found, None otherwise.
        """
        with self._lock:
            return self._symbols_by_id.get(symbol_id)

    def lookup_by_name(self, name: str) -> List[Symbol]:
        """Lookup symbols by exact name match.

        Args:
            name: Symbol name string.

        Returns:
            List of matching Symbol objects.
        """
        with self._lock:
            return list(self._symbols_by_name.get(name, []))

    def lookup_by_file(self, file_path: str) -> List[Symbol]:
        """Lookup all symbols defined in a specific file.

        Args:
            file_path: Target relative file path.

        Returns:
            List of Symbol objects found in that file.
        """
        with self._lock:
            return list(self._symbols_by_file.get(file_path, []))

    def lookup_by_kind(self, kind: SymbolKind) -> List[Symbol]:
        """Lookup symbols filtered by SymbolKind.

        Args:
            kind: Target SymbolKind enum.

        Returns:
            List of matching Symbol objects.
        """
        with self._lock:
            return list(self._symbols_by_kind.get(kind, []))

    def get_children(self, parent_symbol_id: str) -> List[Symbol]:
        """Retrieve direct child symbols of a parent symbol.

        Args:
            parent_symbol_id: Parent symbol unique ID.

        Returns:
            List of child Symbol objects.
        """
        with self._lock:
            return list(self._children_by_parent.get(parent_symbol_id, []))

    def get_hierarchy(self, symbol_id: str) -> List[Symbol]:
        """Traverse upwards from a target symbol to the root parent.

        Args:
            symbol_id: Target symbol ID.

        Returns:
            List of Symbol objects starting from root down to target symbol.
        """
        path: List[Symbol] = []
        current_id: Optional[str] = symbol_id

        with self._lock:
            visited = set()
            while current_id and current_id not in visited:
                sym = self._symbols_by_id.get(current_id)
                if not sym:
                    break
                visited.add(current_id)
                path.append(sym)
                current_id = sym.parent_symbol_id

        path.reverse()
        return path

    def get_all_symbols(self) -> List[Symbol]:
        """Return all indexed symbols.

        Returns:
            List of all Symbol objects.
        """
        with self._lock:
            return list(self._symbols_by_id.values())

    def clear(self) -> None:
        """Clear all entries from the index."""
        with self._lock:
            self._symbols_by_id.clear()
            self._symbols_by_name.clear()
            self._symbols_by_file.clear()
            self._symbols_by_kind.clear()
            self._children_by_parent.clear()
