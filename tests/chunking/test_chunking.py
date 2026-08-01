"""Unit tests for Phase 3: Semantic Chunking Engine."""

from app.chunking.service import ChunkingService
from app.core.types import ChunkType, Language
from app.parsing.service import ParsingEngine


def test_extract_python_chunks() -> None:
    """Test extracting function, class, and method chunks from Python code."""
    code = (
        "def top_func(a, b):\n"
        "    return a + b\n\n"
        "class MyClass:\n"
        "    def method_one(self):\n"
        "        pass\n"
    )
    parser = ParsingEngine()
    chunker = ChunkingService()

    parse_res = parser.parse_code(code, Language.PYTHON, "demo.py")
    chunks = chunker.extract_chunks_from_parse(parse_res, code)

    assert len(chunks) == 3

    names = {c.symbol_name: c for c in chunks}
    assert "top_func" in names
    assert names["top_func"].chunk_type == ChunkType.FUNCTION

    assert "MyClass" in names
    assert names["MyClass"].chunk_type == ChunkType.CLASS

    assert "method_one" in names
    assert names["method_one"].chunk_type == ChunkType.METHOD
    assert names["method_one"].metadata.parent_symbol == "MyClass"


def test_extract_js_chunks() -> None:
    """Test extracting function and class chunks from JavaScript code."""
    code = (
        "function compute(x) {\n"
        "  return x * 2;\n"
        "}\n\n"
        "class Worker {\n"
        "  doWork() {\n"
        "    return true;\n"
        "  }\n"
        "}\n"
    )
    parser = ParsingEngine()
    chunker = ChunkingService()

    parse_res = parser.parse_code(code, Language.JAVASCRIPT, "demo.js")
    chunks = chunker.extract_chunks_from_parse(parse_res, code)

    assert len(chunks) == 3
    symbol_names = [c.symbol_name for c in chunks]
    assert "compute" in symbol_names
    assert "Worker" in symbol_names
    assert "doWork" in symbol_names


def test_chunking_stats_computation() -> None:
    """Test ChunkingService statistics calculation."""
    code = "def f1(): pass\ndef f2(): pass\n"
    parser = ParsingEngine()
    chunker = ChunkingService()

    parse_res = parser.parse_code(code, Language.PYTHON, "test.py")
    chunks = chunker.extract_chunks_from_parse(parse_res, code)
    stats = chunker.compute_stats(chunks)

    assert stats.total_chunks == 2
    assert stats.function_count == 2
    assert stats.average_lines_per_chunk >= 1.0


def test_chunk_exact_code_reconstruction() -> None:
    """Test that extracted chunk source code matches original file lines character-for-character."""
    source_code = (
        "def calculate_total(price: float, tax_rate: float) -> float:\n"
        '    """Calculate total price including tax."""\n'
        "    tax = price * tax_rate\n"
        "    return price + tax\n"
    )
    original_lines = source_code.splitlines()

    parser = ParsingEngine()
    chunker = ChunkingService()

    parse_res = parser.parse_code(source_code, Language.PYTHON, "pricing.py")
    chunks = chunker.extract_chunks_from_parse(parse_res, source_code)

    assert len(chunks) == 1
    chunk = chunks[0]

    # Verify chunk properties
    assert chunk.symbol_name == "calculate_total"
    assert chunk.start_line == 1
    assert chunk.end_line == 4

    # Verify line slice matches source_code in chunk exactly
    expected_slice = "\n".join(original_lines[chunk.start_line - 1 : chunk.end_line])
    assert chunk.source_code == expected_slice
    assert "def calculate_total" in chunk.source_code
    assert "return price + tax" in chunk.source_code

