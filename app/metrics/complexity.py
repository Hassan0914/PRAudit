"""AST Complexity Calculator for Cyclomatic Complexity, Nesting Depth, and Maintainability."""

import math
from typing import Tuple
import tree_sitter

from app.core.logging import setup_logger

logger = setup_logger("metrics.complexity")


class ASTComplexityCalculator:
    """Calculator analyzing AST nodes for complexity, nesting, and maintainability metrics."""

    DECISION_NODE_TYPES = {
        "if_statement",
        "elif_clause",
        "for_statement",
        "while_statement",
        "except_clause",
        "conditional_expression",
        "switch_case",
        "case_clause",
        "catch_clause",
        "binary_expression",  # Checked for '&&' / '||' / 'and' / 'or'
    }

    NESTING_NODE_TYPES = {
        "if_statement",
        "for_statement",
        "while_statement",
        "try_statement",
        "switch_statement",
        "class_definition",
        "function_definition",
    }

    def compute_node_complexity(self, node: tree_sitter.Node) -> int:
        """Calculate Cyclomatic Complexity for an AST node branch.

        Args:
            node: Target tree_sitter.Node.

        Returns:
            Integer complexity value (base 1 + decision points).
        """
        decision_count = 0

        def _traverse(n: tree_sitter.Node) -> None:
            nonlocal decision_count
            if n.type in self.DECISION_NODE_TYPES:
                if n.type == "binary_expression":
                    op_text = n.text.decode("utf-8", errors="ignore")
                    if any(op in op_text for op in ["&&", "||", "and", "or"]):
                        decision_count += 1
                else:
                    decision_count += 1

            for child in n.children:
                _traverse(child)

        _traverse(node)
        return 1 + decision_count

    def compute_max_nesting_depth(self, node: tree_sitter.Node) -> int:
        """Calculate maximum nesting depth within an AST node branch.

        Args:
            node: Target tree_sitter.Node.

        Returns:
            Maximum depth integer.
        """
        def _get_depth(n: tree_sitter.Node, current_depth: int) -> int:
            max_d = current_depth
            next_depth = current_depth + 1 if n.type in self.NESTING_NODE_TYPES else current_depth

            for child in n.children:
                max_d = max(max_d, _get_depth(child, next_depth))

            return max_d

        return _get_depth(node, 0)

    def extract_function_details(self, node: tree_sitter.Node) -> Tuple[int, int]:
        """Extract parameter count and return statement count for a function AST node.

        Args:
            node: Function AST node.

        Returns:
            Tuple of (parameter_count, return_count).
        """
        param_count = 0
        return_count = 0

        def _traverse(n: tree_sitter.Node) -> None:
            nonlocal param_count, return_count
            if n.type in {"parameters", "formal_parameters"}:
                param_count += sum(1 for p in n.children if p.is_named and p.type not in {"(", ")", ","})
            elif n.type in {"return_statement", "return"}:
                return_count += 1

            for child in n.children:
                _traverse(child)

        _traverse(node)
        return param_count, return_count

    def calculate_maintainability_index(
        self, lines_of_code: int, cyclomatic_complexity: int, volume: float = 100.0
    ) -> float:
        """Calculate Maintainability Index (MI) metric.

        MI = max(0, (171 - 5.2 * ln(Volume) - 0.23 * Complexity - 16.2 * ln(LOC)) * 100 / 171)

        Args:
            lines_of_code: Code line count.
            cyclomatic_complexity: Cyclomatic complexity.
            volume: Estimated Halstead volume.

        Returns:
            Float maintainability score between 0.0 and 100.0.
        """
        loc = max(1, lines_of_code)
        vol = max(1.0, volume)
        cc = max(1, cyclomatic_complexity)

        raw_mi = 171.0 - (5.2 * math.log(vol)) - (0.23 * cc) - (16.2 * math.log(loc))
        normalized_mi = max(0.0, min(100.0, (raw_mi * 100.0) / 171.0))
        return round(normalized_mi, 2)
