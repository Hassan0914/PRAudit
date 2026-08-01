"""Data models for Abstract Syntax Trees, parser nodes, errors, and parse results."""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from app.core.types import Language


@dataclass
class ParserError:
    """Represents a syntax or parse error detected within an AST."""

    line: int
    column: int
    node_type: str
    text: str
    message: str


@dataclass
class ASTNode:
    """Standardized wrapper representation of a tree-sitter AST node."""

    type: str
    start_point: tuple[int, int]  # (line, column)
    end_point: tuple[int, int]    # (line, column)
    start_byte: int
    end_byte: int
    text: str
    is_named: bool = True
    is_error: bool = False
    children: List["ASTNode"] = field(default_factory=list)

    @property
    def start_line(self) -> int:
        """1-based start line index."""
        return self.start_point[0] + 1

    @property
    def end_line(self) -> int:
        """1-based end line index."""
        return self.end_point[0] + 1


@dataclass
class ParseResult:
    """Container holding the results of parsing a source code file."""

    file_path: str
    language: Language
    root_node: Optional[ASTNode] = None
    has_syntax_errors: bool = False
    errors: List[ParserError] = field(default_factory=list)
    parse_duration_ms: float = 0.0
    is_success: bool = True
    raw_tree: Optional[Any] = None  # Holds underlying tree_sitter.Tree if needed
