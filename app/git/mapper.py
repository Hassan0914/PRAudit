"""Mapper binding diff changed lines to enclosing functions, classes, and repository symbols."""

from typing import List, Optional
from app.core.logging import setup_logger
from app.git.pr_models import PullRequest, PullRequestFile
from app.symbols.index import SymbolIndex
from app.symbols.models import Symbol, SymbolKind

logger = setup_logger("git.mapper")


class DiffSymbolMapper:
    """Service mapping PR diff lines to repository symbols and scope hierarchy."""

    def map_pr_symbols(self, pr: PullRequest, symbol_index: SymbolIndex) -> PullRequest:
        """Enrich PullRequest line changes with enclosing symbol, function, and class context.

        Args:
            pr: PullRequest model.
            symbol_index: Populated repository SymbolIndex.

        Returns:
            Enriched PullRequest model.
        """
        for pr_file in pr.files:
            file_symbols = symbol_index.lookup_by_file(pr_file.file_path)
            for hunk in pr_file.hunks:
                for line_change in hunk.line_changes:
                    line_no = line_change.line_number
                    sym, func_name, class_name = self._find_enclosing_context(line_no, file_symbols, symbol_index)
                    if sym:
                        line_change.enclosing_symbol = sym.name
                        line_change.enclosing_symbol_id = sym.symbol_id
                    line_change.enclosing_function = func_name
                    line_change.enclosing_class = class_name

        return pr

    def _find_enclosing_context(
        self, line_no: int, file_symbols: List[Symbol], symbol_index: SymbolIndex
    ) -> tuple[Optional[Symbol], Optional[str], Optional[str]]:
        """Find the tightest enclosing symbol, function, and class for a line number."""
        best_sym: Optional[Symbol] = None
        smallest_span = float("inf")
        func_name: Optional[str] = None
        class_name: Optional[str] = None

        for sym in file_symbols:
            if sym.location.start_line <= line_no <= sym.location.end_line:
                span = (sym.location.end_line - sym.location.start_line) + 1
                if span < smallest_span:
                    smallest_span = span
                    best_sym = sym

                if sym.kind == SymbolKind.FUNCTION or sym.kind == SymbolKind.METHOD:
                    func_name = sym.name
                elif sym.kind == SymbolKind.CLASS:
                    class_name = sym.name

        if best_sym and (not func_name or not class_name):
            hierarchy = symbol_index.get_hierarchy(best_sym.symbol_id)
            for h_sym in hierarchy:
                if h_sym.kind in {SymbolKind.FUNCTION, SymbolKind.METHOD}:
                    func_name = h_sym.name
                elif h_sym.kind == SymbolKind.CLASS:
                    class_name = h_sym.name

        return best_sym, func_name, class_name
