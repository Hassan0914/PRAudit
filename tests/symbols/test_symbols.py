"""Unit tests for Phase 4: Symbol Extraction Engine."""

from app.core.types import Language, SymbolKind
from app.parsing.service import ParsingEngine
from app.symbols.index import SymbolIndex
from app.symbols.service import SymbolService


def test_extract_python_symbols() -> None:
    """Test extracting functions, classes, methods, imports, and variables from Python code."""
    code = (
        "import os\n"
        "from sys import version\n\n"
        "MAX_RETRY = 3\n\n"
        "def process():\n"
        "    pass\n\n"
        "class Service:\n"
        "    def run(self):\n"
        "        pass\n"
    )
    parser = ParsingEngine()
    service = SymbolService()

    parse_res = parser.parse_code(code, Language.PYTHON, "app.py")
    symbols = service.extract_symbols_from_parse(parse_res, code)

    # Verify extracted symbol kinds
    kinds = [s.kind for s in symbols]
    assert SymbolKind.MODULE in kinds
    assert SymbolKind.IMPORT in kinds
    assert SymbolKind.CONSTANT in kinds
    assert SymbolKind.FUNCTION in kinds
    assert SymbolKind.CLASS in kinds
    assert SymbolKind.METHOD in kinds

    # Verify index lookups
    index = service.index
    assert len(index.lookup_by_name("process")) == 1
    assert len(index.lookup_by_name("Service")) == 1
    assert len(index.lookup_by_name("MAX_RETRY")) == 1
    assert len(index.lookup_by_kind(SymbolKind.IMPORT)) == 2


def test_symbol_hierarchy_traversal() -> None:
    """Test traversing parent-child hierarchy in SymbolIndex."""
    code = (
        "class Outer:\n"
        "    def inner_method(self):\n"
        "        pass\n"
    )
    parser = ParsingEngine()
    service = SymbolService()

    parse_res = parser.parse_code(code, Language.PYTHON, "hierarchy.py")
    service.extract_symbols_from_parse(parse_res, code)

    method_symbols = service.index.lookup_by_name("inner_method")
    assert len(method_symbols) == 1
    method_sym = method_symbols[0]

    # Traversal up to module root
    hierarchy = service.index.get_hierarchy(method_sym.symbol_id)
    assert len(hierarchy) == 3  # Module -> Class -> Method
    assert hierarchy[0].kind == SymbolKind.MODULE
    assert hierarchy[1].name == "Outer"
    assert hierarchy[2].name == "inner_method"
