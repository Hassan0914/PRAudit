"""AST Validator and Node Transformer.

Traverses Tree-sitter syntax trees, validates node integrity, builds typed ASTNode
hierarchies, and extracts syntax error details.
"""

from typing import List, Tuple
import tree_sitter

from app.core.logging import setup_logger
from app.parsing.models import ASTNode, ParserError

logger = setup_logger("parsing.validator")


class ASTValidator:
    """Validator for inspecting Tree-sitter AST nodes and constructing ASTNode trees."""

    def build_ast_node(
        self, node: tree_sitter.Node, source_bytes: bytes
    ) -> Tuple[ASTNode, List[ParserError]]:
        """Recursively build a typed ASTNode and collect any syntax errors.

        Args:
            node: Raw tree_sitter.Node.
            source_bytes: Source code byte sequence.

        Returns:
            Tuple of (root ASTNode, list of ParserError).
        """
        errors: List[ParserError] = []

        def _traverse(n: tree_sitter.Node) -> ASTNode:
            is_error = n.type == "ERROR" or n.is_missing or n.has_error

            if n.type == "ERROR" or n.is_missing:
                start_line = n.start_point[0] + 1
                start_col = n.start_point[1] + 1
                snippet = source_bytes[n.start_byte : n.end_byte].decode("utf-8", errors="ignore").strip()
                msg = f"Syntax error at line {start_line}, col {start_col}"
                if n.is_missing:
                    msg = f"Missing syntax element near line {start_line}, col {start_col}"

                errors.append(
                    ParserError(
                        line=start_line,
                        column=start_col,
                        node_type=n.type,
                        text=snippet[:100],
                        message=msg,
                    )
                )

            node_text = source_bytes[n.start_byte : n.end_byte].decode("utf-8", errors="ignore")

            children: List[ASTNode] = []
            for child in n.children:
                children.append(_traverse(child))

            return ASTNode(
                type=n.type,
                start_point=(n.start_point[0], n.start_point[1]),
                end_point=(n.end_point[0], n.end_point[1]),
                start_byte=n.start_byte,
                end_byte=n.end_byte,
                text=node_text,
                is_named=n.is_named,
                is_error=is_error,
                children=children,
            )

        root_ast_node = _traverse(node)
        return root_ast_node, errors
