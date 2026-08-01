"""Symbol extraction service and stats aggregator."""

from typing import List, Optional
from app.core.exceptions import SymbolExtractionError
from app.core.logging import setup_logger
from app.core.types import SymbolKind
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.symbols.extractor import SymbolExtractorFactory
from app.symbols.index import SymbolIndex
from app.symbols.models import Symbol, SymbolStats

logger = setup_logger("symbols.service")


class SymbolService:
    """Service for extracting programming symbols and generating symbol analytics."""

    def __init__(self, index: Optional[SymbolIndex] = None) -> None:
        """Initialize SymbolService.

        Args:
            index: Optional existing SymbolIndex instance.
        """
        self.index = index or SymbolIndex()

    def extract_symbols_from_parse(
        self, parse_result: ParseResult, source_code: str
    ) -> List[Symbol]:
        """Extract symbols from parse result and source code string.

        Args:
            parse_result: AST ParseResult.
            source_code: Full text of source code.

        Returns:
            List of extracted Symbol instances.
        """
        if not source_code or not source_code.strip():
            return []

        try:
            extractor = SymbolExtractorFactory.get_extractor(parse_result.language)
            symbols = extractor.extract_symbols(parse_result, source_code)
            self.index.add_symbols(symbols)
            logger.debug(
                "Extracted %d symbols for file %s", len(symbols), parse_result.file_path
            )
            return symbols
        except Exception as exc:
            logger.error(
                "Error extracting symbols for file %s: %s", parse_result.file_path, exc, exc_info=True
            )
            raise SymbolExtractionError(
                f"Failed to extract symbols for file '{parse_result.file_path}': {exc}"
            ) from exc

    def extract_symbols_from_file(
        self, source_file: SourceFile, parse_result: ParseResult
    ) -> List[Symbol]:
        """Extract symbols from a SourceFile.

        Args:
            source_file: SourceFile model.
            parse_result: Output from ParsingEngine.

        Returns:
            List of Symbol objects.
        """
        try:
            source_code = source_file.absolute_path.read_text(encoding="utf-8", errors="ignore")
            return self.extract_symbols_from_parse(parse_result, source_code)
        except Exception as exc:
            logger.warning(
                "Could not read source code for file %s during symbol extraction: %s",
                source_file.relative_path,
                exc,
            )
            return []

    def compute_stats(self, symbols: Optional[List[Symbol]] = None) -> SymbolStats:
        """Compute aggregate symbol statistics.

        Args:
            symbols: Optional explicit list of symbols. If omitted, uses all symbols in the index.

        Returns:
            Populated SymbolStats model.
        """
        target_symbols = symbols if symbols is not None else self.index.get_all_symbols()
        stats = SymbolStats(total_symbols=len(target_symbols))

        for sym in target_symbols:
            if sym.kind == SymbolKind.FUNCTION:
                stats.function_count += 1
            elif sym.kind == SymbolKind.CLASS:
                stats.class_count += 1
            elif sym.kind == SymbolKind.METHOD:
                stats.method_count += 1
            elif sym.kind == SymbolKind.IMPORT:
                stats.import_count += 1
            elif sym.kind == SymbolKind.EXPORT:
                stats.export_count += 1
            elif sym.kind == SymbolKind.VARIABLE:
                stats.variable_count += 1
            elif sym.kind == SymbolKind.CONSTANT:
                stats.constant_count += 1
            elif sym.kind == SymbolKind.MODULE:
                stats.module_count += 1

        return stats
