"""Symbol extraction implementations for Python, JavaScript, and generic code."""

from abc import ABC, abstractmethod
import hashlib
import re
from typing import List, Optional
import tree_sitter

from app.core.logging import setup_logger
from app.core.types import Language, SymbolKind
from app.parsing.models import ParseResult
from app.symbols.models import Symbol, SymbolLocation

logger = setup_logger("symbols.extractor")


def generate_symbol_id(file_path: str, kind: SymbolKind, name: str, start_line: int, start_col: int) -> str:
    """Generate a unique symbol ID.

    Args:
        file_path: Relative file path.
        kind: SymbolKind enum.
        name: Name of symbol.
        start_line: 1-based start line.
        start_col: 1-based start column.

    Returns:
        Hexadecimal hash string identifier.
    """
    raw_key = f"{file_path}:{kind.value}:{name}:{start_line}:{start_col}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


class BaseSymbolExtractor(ABC):
    """Abstract base class for language-specific symbol extractors."""

    @abstractmethod
    def extract_symbols(self, parse_result: ParseResult, source_code: str) -> List[Symbol]:
        """Extract symbols from a parse result and source code.

        Args:
            parse_result: Output of ParsingEngine.
            source_code: Source code text string.

        Returns:
            List of extracted Symbol instances.
        """
        pass


class PythonSymbolExtractor(BaseSymbolExtractor):
    """Symbol extractor for Python source files."""

    def extract_symbols(self, parse_result: ParseResult, source_code: str) -> List[Symbol]:
        """Extract Python functions, classes, methods, imports, variables, and constants."""
        symbols: List[Symbol] = []
        if not parse_result.raw_tree or not parse_result.raw_tree.root_node:
            return symbols

        file_path = parse_result.file_path
        root_node = parse_result.raw_tree.root_node

        # Module level symbol
        module_id = generate_symbol_id(file_path, SymbolKind.MODULE, file_path, 1, 1)
        symbols.append(
            Symbol(
                symbol_id=module_id,
                name=file_path,
                kind=SymbolKind.MODULE,
                file_path=file_path,
                language=Language.PYTHON,
                location=SymbolLocation(
                    file_path=file_path,
                    start_line=1,
                    end_line=root_node.end_point[0] + 1,
                    start_column=1,
                    end_column=root_node.end_point[1] + 1,
                ),
            )
        )

        def _traverse(node: tree_sitter.Node, parent_id: Optional[str] = module_id, scope: str = "") -> None:
            if node.type == "import_statement":
                # e.g., import os, sys
                snippet = node.text.decode("utf-8", errors="ignore").strip()
                s_id = generate_symbol_id(file_path, SymbolKind.IMPORT, snippet, node.start_point[0] + 1, node.start_point[1] + 1)
                symbols.append(
                    Symbol(
                        symbol_id=s_id,
                        name=snippet,
                        kind=SymbolKind.IMPORT,
                        file_path=file_path,
                        language=Language.PYTHON,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        parent_symbol_id=parent_id,
                        scope_path=scope or file_path,
                    )
                )

            elif node.type == "import_from_statement":
                # e.g., from typing import List, Dict
                snippet = node.text.decode("utf-8", errors="ignore").strip()
                s_id = generate_symbol_id(file_path, SymbolKind.IMPORT, snippet, node.start_point[0] + 1, node.start_point[1] + 1)
                symbols.append(
                    Symbol(
                        symbol_id=s_id,
                        name=snippet,
                        kind=SymbolKind.IMPORT,
                        file_path=file_path,
                        language=Language.PYTHON,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        parent_symbol_id=parent_id,
                        scope_path=scope or file_path,
                    )
                )

            elif node.type == "class_definition":
                class_name = "<anonymous>"
                for child in node.children:
                    if child.type == "identifier":
                        class_name = child.text.decode("utf-8", errors="ignore")
                        break

                c_id = generate_symbol_id(file_path, SymbolKind.CLASS, class_name, node.start_point[0] + 1, node.start_point[1] + 1)
                new_scope = f"{scope}.{class_name}" if scope else class_name

                # Extract docstring if first node in body block is expression string
                doc = None
                for child in node.children:
                    if child.type == "block" and child.children:
                        first_expr = child.children[0]
                        if first_expr.type == "expression_statement":
                            doc = first_expr.text.decode("utf-8", errors="ignore").strip()

                symbols.append(
                    Symbol(
                        symbol_id=c_id,
                        name=class_name,
                        kind=SymbolKind.CLASS,
                        file_path=file_path,
                        language=Language.PYTHON,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        docstring=doc,
                        parent_symbol_id=parent_id,
                        scope_path=new_scope,
                    )
                )
                for child in node.children:
                    _traverse(child, parent_id=c_id, scope=new_scope)
                return

            elif node.type == "function_definition":
                func_name = "<anonymous>"
                signature = None
                for child in node.children:
                    if child.type == "identifier":
                        func_name = child.text.decode("utf-8", errors="ignore")
                    elif child.type == "parameters":
                        signature = child.text.decode("utf-8", errors="ignore")

                is_method = scope and "." in scope or (parent_id and any(s.symbol_id == parent_id and s.kind == SymbolKind.CLASS for s in symbols))
                kind = SymbolKind.METHOD if is_method else SymbolKind.FUNCTION
                f_id = generate_symbol_id(file_path, kind, func_name, node.start_point[0] + 1, node.start_point[1] + 1)
                new_scope = f"{scope}.{func_name}" if scope else func_name

                doc = None
                for child in node.children:
                    if child.type == "block" and child.children:
                        first_expr = child.children[0]
                        if first_expr.type == "expression_statement":
                            doc = first_expr.text.decode("utf-8", errors="ignore").strip()

                symbols.append(
                    Symbol(
                        symbol_id=f_id,
                        name=func_name,
                        kind=kind,
                        file_path=file_path,
                        language=Language.PYTHON,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        signature=signature,
                        docstring=doc,
                        parent_symbol_id=parent_id,
                        scope_path=new_scope,
                    )
                )
                for child in node.children:
                    _traverse(child, parent_id=f_id, scope=new_scope)
                return

            elif node.type == "expression_statement" and scope == "":
                # Top level module variable or constant assignment
                for child in node.children:
                    if child.type == "assignment":
                        left = child.children[0] if child.children else None
                        if left and left.type == "identifier":
                            var_name = left.text.decode("utf-8", errors="ignore")
                            kind = SymbolKind.CONSTANT if var_name.isupper() else SymbolKind.VARIABLE
                            v_id = generate_symbol_id(file_path, kind, var_name, node.start_point[0] + 1, node.start_point[1] + 1)
                            symbols.append(
                                Symbol(
                                    symbol_id=v_id,
                                    name=var_name,
                                    kind=kind,
                                    file_path=file_path,
                                    language=Language.PYTHON,
                                    location=SymbolLocation(
                                        file_path=file_path,
                                        start_line=node.start_point[0] + 1,
                                        end_line=node.end_point[0] + 1,
                                        start_column=node.start_point[1] + 1,
                                        end_column=node.end_point[1] + 1,
                                    ),
                                    parent_symbol_id=module_id,
                                    scope_path=file_path,
                                )
                            )

            for child in node.children:
                _traverse(child, parent_id=parent_id, scope=scope)

        _traverse(root_node)
        return symbols


class JavaScriptSymbolExtractor(BaseSymbolExtractor):
    """Symbol extractor for JavaScript and TypeScript source files."""

    def extract_symbols(self, parse_result: ParseResult, source_code: str) -> List[Symbol]:
        """Extract JS/TS functions, classes, methods, imports, exports, and variables."""
        symbols: List[Symbol] = []
        if not parse_result.raw_tree or not parse_result.raw_tree.root_node:
            return symbols

        file_path = parse_result.file_path
        root_node = parse_result.raw_tree.root_node

        module_id = generate_symbol_id(file_path, SymbolKind.MODULE, file_path, 1, 1)
        symbols.append(
            Symbol(
                symbol_id=module_id,
                name=file_path,
                kind=SymbolKind.MODULE,
                file_path=file_path,
                language=parse_result.language,
                location=SymbolLocation(
                    file_path=file_path,
                    start_line=1,
                    end_line=root_node.end_point[0] + 1,
                    start_column=1,
                    end_column=root_node.end_point[1] + 1,
                ),
            )
        )

        def _traverse(node: tree_sitter.Node, parent_id: Optional[str] = module_id, scope: str = "") -> None:
            if node.type in {"import_statement", "export_statement"}:
                snippet = node.text.decode("utf-8", errors="ignore").strip()
                kind = SymbolKind.IMPORT if node.type == "import_statement" else SymbolKind.EXPORT
                s_id = generate_symbol_id(file_path, kind, snippet, node.start_point[0] + 1, node.start_point[1] + 1)
                symbols.append(
                    Symbol(
                        symbol_id=s_id,
                        name=snippet[:50],
                        kind=kind,
                        file_path=file_path,
                        language=parse_result.language,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        parent_symbol_id=parent_id,
                        scope_path=scope or file_path,
                    )
                )

            elif node.type == "class_declaration":
                class_name = "<anonymous>"
                for child in node.children:
                    if child.type == "identifier":
                        class_name = child.text.decode("utf-8", errors="ignore")
                        break

                c_id = generate_symbol_id(file_path, SymbolKind.CLASS, class_name, node.start_point[0] + 1, node.start_point[1] + 1)
                new_scope = f"{scope}.{class_name}" if scope else class_name
                symbols.append(
                    Symbol(
                        symbol_id=c_id,
                        name=class_name,
                        kind=SymbolKind.CLASS,
                        file_path=file_path,
                        language=parse_result.language,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        parent_symbol_id=parent_id,
                        scope_path=new_scope,
                    )
                )
                for child in node.children:
                    _traverse(child, parent_id=c_id, scope=new_scope)
                return

            elif node.type in {"function_declaration", "method_definition"}:
                func_name = "<anonymous>"
                for child in node.children:
                    if child.type in {"identifier", "property_identifier"}:
                        func_name = child.text.decode("utf-8", errors="ignore")
                        break

                kind = SymbolKind.METHOD if node.type == "method_definition" else SymbolKind.FUNCTION
                f_id = generate_symbol_id(file_path, kind, func_name, node.start_point[0] + 1, node.start_point[1] + 1)
                new_scope = f"{scope}.{func_name}" if scope else func_name
                symbols.append(
                    Symbol(
                        symbol_id=f_id,
                        name=func_name,
                        kind=kind,
                        file_path=file_path,
                        language=parse_result.language,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1] + 1,
                            end_column=node.end_point[1] + 1,
                        ),
                        parent_symbol_id=parent_id,
                        scope_path=new_scope,
                    )
                )
                for child in node.children:
                    _traverse(child, parent_id=f_id, scope=new_scope)
                return

            for child in node.children:
                _traverse(child, parent_id=parent_id, scope=scope)

        _traverse(root_node)
        return symbols


class GenericSymbolExtractor(BaseSymbolExtractor):
    """Regex fallback symbol extractor for unsupported AST languages."""

    def extract_symbols(self, parse_result: ParseResult, source_code: str) -> List[Symbol]:
        """Extract generic function/class signatures using regex."""
        symbols: List[Symbol] = []
        lines = source_code.splitlines()
        file_path = parse_result.file_path

        func_pattern = re.compile(r"^\s*(def|function|fn|func)\s+([a-zA-Z_]\w*)")
        class_pattern = re.compile(r"^\s*(class|struct|interface)\s+([a-zA-Z_]\w*)")

        for idx, line in enumerate(lines, start=1):
            f_match = func_pattern.search(line)
            if f_match:
                name = f_match.group(2)
                s_id = generate_symbol_id(file_path, SymbolKind.FUNCTION, name, idx, 1)
                symbols.append(
                    Symbol(
                        symbol_id=s_id,
                        name=name,
                        kind=SymbolKind.FUNCTION,
                        file_path=file_path,
                        language=parse_result.language,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=idx,
                            end_line=idx,
                            start_column=1,
                            end_column=len(line) + 1,
                        ),
                    )
                )
                continue

            c_match = class_pattern.search(line)
            if c_match:
                name = c_match.group(2)
                s_id = generate_symbol_id(file_path, SymbolKind.CLASS, name, idx, 1)
                symbols.append(
                    Symbol(
                        symbol_id=s_id,
                        name=name,
                        kind=SymbolKind.CLASS,
                        file_path=file_path,
                        language=parse_result.language,
                        location=SymbolLocation(
                            file_path=file_path,
                            start_line=idx,
                            end_line=idx,
                            start_column=1,
                            end_column=len(line) + 1,
                        ),
                    )
                )

        return symbols


class SymbolExtractorFactory:
    """Factory providing language-specific symbol extractors."""

    _extractors = {
        Language.PYTHON: PythonSymbolExtractor(),
        Language.JAVASCRIPT: JavaScriptSymbolExtractor(),
        Language.TYPESCRIPT: JavaScriptSymbolExtractor(),
    }
    _generic = GenericSymbolExtractor()

    @classmethod
    def get_extractor(cls, language: Language) -> BaseSymbolExtractor:
        """Get symbol extractor for given language.

        Args:
            language: Language enum.

        Returns:
            BaseSymbolExtractor implementation.
        """
        return cls._extractors.get(language, cls._generic)
