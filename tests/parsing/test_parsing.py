"""Unit tests for Phase 2: Parsing Engine."""

from app.core.types import Language
from app.parsing.languages import language_registry
from app.parsing.factory import parser_factory
from app.parsing.service import ParsingEngine
from app.repository.models import SourceFile


def test_language_registry_support() -> None:
    """Test LanguageRegistry built-in language registration."""
    assert language_registry.is_supported(Language.PYTHON) is True
    assert language_registry.is_supported(Language.JAVASCRIPT) is True


def test_parser_factory_caching() -> None:
    """Test ParserFactory returns cached Parser instance."""
    p1 = parser_factory.create_parser(Language.PYTHON)
    p2 = parser_factory.create_parser(Language.PYTHON)
    assert p1 is p2


def test_parse_valid_python_code() -> None:
    """Test parsing valid Python code into AST."""
    engine = ParsingEngine()
    code = "def foo(x):\n    return x * 2\n"
    res = engine.parse_code(code, Language.PYTHON, "test.py")

    assert res.is_success is True
    assert res.has_syntax_errors is False
    assert res.root_node is not None
    assert res.root_node.type == "module"
    assert len(res.errors) == 0


def test_parse_malformed_code_recovers_gracefully() -> None:
    """Test parsing malformed code detects syntax errors without crashing."""
    engine = ParsingEngine()
    bad_code = "def foo(: def\n"
    res = engine.parse_code(bad_code, Language.PYTHON, "bad.py")

    assert res.is_success is True
    assert res.has_syntax_errors is True
    assert len(res.errors) > 0
    assert res.errors[0].line >= 1


def test_parse_unsupported_language() -> None:
    """Test parsing an unsupported language handles gracefully."""
    engine = ParsingEngine()
    res = engine.parse_code("hello world", Language.UNKNOWN, "test.txt")

    assert res.is_success is False
    assert len(res.errors) == 1
    assert res.errors[0].node_type == "UNSUPPORTED_LANGUAGE"
