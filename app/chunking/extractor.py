"""Semantic chunk extraction implementations for Python, JavaScript, and generic code."""

from abc import ABC, abstractmethod
import hashlib
from typing import List, Optional
import tree_sitter

from app.core.logging import setup_logger
from app.core.types import ChunkType, Language
from app.chunking.models import ChunkMetadata, CodeChunk
from app.parsing.models import ASTNode, ParseResult

logger = setup_logger("chunking.extractor")


def generate_chunk_id(file_path: str, symbol_name: str, start_line: int, end_line: int) -> str:
    """Generate a deterministic unique chunk ID.

    Args:
        file_path: File path.
        symbol_name: Extracted symbol name.
        start_line: 1-based start line.
        end_line: 1-based end line.

    Returns:
        Hexadecimal hash string identifier.
    """
    raw_key = f"{file_path}:{symbol_name}:{start_line}:{end_line}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


class BaseChunkExtractor(ABC):
    """Abstract base class for language-specific semantic chunk extractors."""

    @abstractmethod
    def extract_chunks(self, parse_result: ParseResult, source_code: str) -> List[CodeChunk]:
        """Extract semantic chunks from a parse result and source code.

        Args:
            parse_result: The AST parse result of the file.
            source_code: Full string source code of the file.

        Returns:
            List of extracted CodeChunk objects.
        """
        pass


class PythonChunkExtractor(BaseChunkExtractor):
    """Extractor for Python AST trees."""

    def extract_chunks(self, parse_result: ParseResult, source_code: str) -> List[CodeChunk]:
        """Extract Python functions, classes, and methods."""
        chunks: List[CodeChunk] = []

        if not parse_result.raw_tree or not parse_result.raw_tree.root_node:
            return chunks

        lines = source_code.splitlines()
        root_node = parse_result.raw_tree.root_node
        file_path = parse_result.file_path

        def _traverse(node: tree_sitter.Node, parent_class: Optional[str] = None, parent_chunk_id: Optional[str] = None) -> None:
            if node.type in {"function_definition", "class_definition"}:
                symbol_name = "<anonymous>"
                # Extract identifier
                for child in node.children:
                    if child.type == "identifier":
                        symbol_name = child.text.decode("utf-8", errors="ignore")
                        break

                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                # Slice source lines accurately
                chunk_lines = lines[node.start_point[0] : node.end_point[0] + 1]
                chunk_code = "\n".join(chunk_lines)

                if node.type == "class_definition":
                    chunk_type = ChunkType.CLASS
                    chunk_id = generate_chunk_id(file_path, symbol_name, start_line, end_line)
                    metadata = ChunkMetadata(
                        node_type="class_definition",
                        parent_symbol=parent_class,
                    )
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=file_path,
                            language=Language.PYTHON,
                            chunk_type=chunk_type,
                            symbol_name=symbol_name,
                            source_code=chunk_code,
                            start_line=start_line,
                            end_line=end_line,
                            parent_chunk_id=parent_chunk_id,
                            metadata=metadata,
                        )
                    )
                    # Traverse children inside class body with updated parent_class context
                    for child in node.children:
                        _traverse(child, parent_class=symbol_name, parent_chunk_id=chunk_id)
                    return

                elif node.type == "function_definition":
                    chunk_type = ChunkType.METHOD if parent_class else ChunkType.FUNCTION
                    chunk_id = generate_chunk_id(file_path, symbol_name, start_line, end_line)

                    # Extract parameters
                    params: List[str] = []
                    for child in node.children:
                        if child.type == "parameters":
                            params = [
                                p.text.decode("utf-8", errors="ignore")
                                for p in child.children
                                if p.is_named and p.type not in {"(", ")", ","}
                            ]

                    metadata = ChunkMetadata(
                        node_type="function_definition",
                        parent_symbol=parent_class,
                        parameters=params,
                    )
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=file_path,
                            language=Language.PYTHON,
                            chunk_type=chunk_type,
                            symbol_name=symbol_name,
                            source_code=chunk_code,
                            start_line=start_line,
                            end_line=end_line,
                            parent_chunk_id=parent_chunk_id,
                            metadata=metadata,
                        )
                    )
                    # Traverse children inside function if any nested functions exist
                    for child in node.children:
                        _traverse(child, parent_class=parent_class, parent_chunk_id=chunk_id)
                    return

            for child in node.children:
                _traverse(child, parent_class=parent_class, parent_chunk_id=parent_chunk_id)

        _traverse(root_node)
        return chunks


class JavaScriptChunkExtractor(BaseChunkExtractor):
    """Extractor for JavaScript / TypeScript AST trees."""

    def extract_chunks(self, parse_result: ParseResult, source_code: str) -> List[CodeChunk]:
        """Extract JavaScript functions, classes, arrow functions, and methods."""
        chunks: List[CodeChunk] = []

        if not parse_result.raw_tree or not parse_result.raw_tree.root_node:
            return chunks

        lines = source_code.splitlines()
        root_node = parse_result.raw_tree.root_node
        file_path = parse_result.file_path

        def _traverse(node: tree_sitter.Node, parent_class: Optional[str] = None, parent_chunk_id: Optional[str] = None) -> None:
            if node.type in {"function_declaration", "class_declaration", "method_definition", "lexical_declaration"}:
                symbol_name = "<anonymous>"
                node_type = node.type

                if node.type in {"function_declaration", "class_declaration"}:
                    for child in node.children:
                        if child.type == "identifier":
                            symbol_name = child.text.decode("utf-8", errors="ignore")
                            break
                elif node.type == "method_definition":
                    for child in node.children:
                        if child.type in {"property_identifier", "identifier"}:
                            symbol_name = child.text.decode("utf-8", errors="ignore")
                            break
                elif node.type == "lexical_declaration":
                    # Check for arrow function assignment e.g. const foo = () => {}
                    has_arrow = False
                    for declarator in node.children:
                        if declarator.type == "variable_declarator":
                            for child in declarator.children:
                                if child.type == "identifier":
                                    symbol_name = child.text.decode("utf-8", errors="ignore")
                                if child.type in {"arrow_function", "function"}:
                                    has_arrow = True
                    if not has_arrow:
                        # Skip normal variable declarations
                        for child in node.children:
                            _traverse(child, parent_class, parent_chunk_id)
                        return

                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                chunk_lines = lines[node.start_point[0] : node.end_point[0] + 1]
                chunk_code = "\n".join(chunk_lines)

                if node.type == "class_declaration":
                    chunk_type = ChunkType.CLASS
                    chunk_id = generate_chunk_id(file_path, symbol_name, start_line, end_line)
                    metadata = ChunkMetadata(node_type="class_declaration", parent_symbol=parent_class)
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=file_path,
                            language=parse_result.language,
                            chunk_type=chunk_type,
                            symbol_name=symbol_name,
                            source_code=chunk_code,
                            start_line=start_line,
                            end_line=end_line,
                            parent_chunk_id=parent_chunk_id,
                            metadata=metadata,
                        )
                    )
                    for child in node.children:
                        _traverse(child, parent_class=symbol_name, parent_chunk_id=chunk_id)
                    return

                elif node.type in {"function_declaration", "method_definition", "lexical_declaration"}:
                    chunk_type = ChunkType.METHOD if (parent_class or node.type == "method_definition") else ChunkType.FUNCTION
                    chunk_id = generate_chunk_id(file_path, symbol_name, start_line, end_line)
                    metadata = ChunkMetadata(node_type=node.type, parent_symbol=parent_class)
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=file_path,
                            language=parse_result.language,
                            chunk_type=chunk_type,
                            symbol_name=symbol_name,
                            source_code=chunk_code,
                            start_line=start_line,
                            end_line=end_line,
                            parent_chunk_id=parent_chunk_id,
                            metadata=metadata,
                        )
                    )
                    for child in node.children:
                        _traverse(child, parent_class=parent_class, parent_chunk_id=chunk_id)
                    return

            for child in node.children:
                _traverse(child, parent_class=parent_class, parent_chunk_id=parent_chunk_id)

        _traverse(root_node)
        return chunks


class GenericChunkExtractor(BaseChunkExtractor):
    """Fallback chunk extractor for unsupported AST languages."""

    def extract_chunks(self, parse_result: ParseResult, source_code: str) -> List[CodeChunk]:
        """Extract top-level block chunks using empty-line delimiters."""
        chunks: List[CodeChunk] = []
        lines = source_code.splitlines()
        if not lines:
            return chunks

        current_block: List[str] = []
        start_line = 1

        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                if current_block:
                    end_line = idx - 1
                    block_text = "\n".join(current_block)
                    chunk_id = generate_chunk_id(parse_result.file_path, f"block_{start_line}", start_line, end_line)
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=parse_result.file_path,
                            language=parse_result.language,
                            chunk_type=ChunkType.BLOCK,
                            symbol_name=f"block_{start_line}_{end_line}",
                            source_code=block_text,
                            start_line=start_line,
                            end_line=end_line,
                            metadata=ChunkMetadata(node_type="generic_block"),
                        )
                    )
                    current_block = []
            else:
                if not current_block:
                    start_line = idx
                current_block.append(line)

        if current_block:
            end_line = len(lines)
            block_text = "\n".join(current_block)
            chunk_id = generate_chunk_id(parse_result.file_path, f"block_{start_line}", start_line, end_line)
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=parse_result.file_path,
                    language=parse_result.language,
                    chunk_type=ChunkType.BLOCK,
                    symbol_name=f"block_{start_line}_{end_line}",
                    source_code=block_text,
                    start_line=start_line,
                    end_line=end_line,
                    metadata=ChunkMetadata(node_type="generic_block"),
                )
            )

        return chunks


class ChunkExtractorFactory:
    """Factory to retrieve appropriate extractor for a programming language."""

    _extractors = {
        Language.PYTHON: PythonChunkExtractor(),
        Language.JAVASCRIPT: JavaScriptChunkExtractor(),
        Language.TYPESCRIPT: JavaScriptChunkExtractor(),
    }
    _generic = GenericChunkExtractor()

    @classmethod
    def get_extractor(cls, language: Language) -> BaseChunkExtractor:
        """Get chunk extractor for language.

        Args:
            language: Language enum.

        Returns:
            BaseChunkExtractor implementation.
        """
        return cls._extractors.get(language, cls._generic)
