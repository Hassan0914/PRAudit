"""Metrics Engine calculating function, class, file, and repository level metrics."""

from typing import List, Optional, Tuple
import tree_sitter

from app.core.logging import setup_logger
from app.metrics.complexity import ASTComplexityCalculator
from app.metrics.models import (
    ClassMetrics,
    FileMetrics,
    FunctionMetrics,
    RepositoryMetrics,
)
from app.parsing.models import ParseResult
from app.repository.models import SourceFile

logger = setup_logger("metrics.calculator")


class MetricsEngine:
    """Master engine for evaluating software quality and complexity metrics."""

    def __init__(self) -> None:
        """Initialize MetricsEngine."""
        self.calculator = ASTComplexityCalculator()

    def analyze_repository_metrics(
        self, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> RepositoryMetrics:
        """Calculate repository-wide metrics across all source files.

        Args:
            source_files: Discovered source files.
            parse_results: AST parse results.

        Returns:
            RepositoryMetrics container.
        """
        logger.info("Computing code metrics across repository files...")

        parse_map = {pr.file_path: pr for pr in parse_results}
        repo_metrics = RepositoryMetrics(total_files=len(source_files))

        file_metrics_map = {}
        total_loc = 0
        total_code_lines = 0
        total_comment_lines = 0
        total_funcs = 0
        total_classes = 0
        sum_complexity = 0
        sum_maintainability = 0.0

        for sf in source_files:
            pr = parse_map.get(sf.relative_path)
            fm = self.analyze_file_metrics(sf, pr)
            file_metrics_map[sf.relative_path] = fm

            total_loc += fm.total_lines
            total_code_lines += fm.code_lines
            total_comment_lines += fm.comment_lines
            total_funcs += len(fm.functions)
            total_classes += len(fm.classes)
            sum_complexity += fm.total_complexity
            sum_maintainability += fm.maintainability_index

        repo_metrics.total_lines = total_loc
        repo_metrics.total_code_lines = total_code_lines
        repo_metrics.total_comment_lines = total_comment_lines
        repo_metrics.total_functions = total_funcs
        repo_metrics.total_classes = total_classes

        n_files = len(source_files)
        repo_metrics.average_cyclomatic_complexity = (
            round(sum_complexity / max(1, total_funcs + total_classes), 2)
        )
        repo_metrics.average_maintainability_index = (
            round(sum_maintainability / max(1, n_files), 2)
        )
        repo_metrics.file_metrics = file_metrics_map

        logger.info(
            "Metrics calculation completed: %d total lines, %d functions, avg complexity: %.2f",
            total_loc,
            total_funcs,
            repo_metrics.average_cyclomatic_complexity,
        )

        return repo_metrics

    def analyze_file_metrics(
        self, source_file: SourceFile, parse_result: Optional[ParseResult]
    ) -> FileMetrics:
        """Calculate quality metrics for a single source file.

        Args:
            source_file: SourceFile model.
            parse_result: Optional AST ParseResult.

        Returns:
            FileMetrics container.
        """
        code_lines, comment_lines, blank_lines = self._count_line_types(source_file)
        funcs: List[FunctionMetrics] = []
        classes: List[ClassMetrics] = []

        if parse_result and parse_result.raw_tree and parse_result.raw_tree.root_node:
            root = parse_result.raw_tree.root_node
            funcs, classes = self._extract_ast_metrics(root, source_file.relative_path)

        total_comp = sum(f.cyclomatic_complexity for f in funcs) + sum(c.total_complexity for c in classes)
        max_comp = max([f.cyclomatic_complexity for f in funcs] + [0])
        avg_func_comp = round(total_comp / len(funcs), 2) if funcs else 1.0

        maintainability = self.calculator.calculate_maintainability_index(
            lines_of_code=code_lines,
            cyclomatic_complexity=max(1, total_comp),
        )

        return FileMetrics(
            file_path=source_file.relative_path,
            total_lines=source_file.line_count,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            total_complexity=total_comp,
            average_function_complexity=avg_func_comp,
            max_cyclomatic_complexity=max_comp,
            maintainability_index=maintainability,
            functions=funcs,
            classes=classes,
        )

    def _count_line_types(self, source_file: SourceFile) -> Tuple[int, int, int]:
        """Classify lines into code lines, comment lines, and blank lines."""
        try:
            text = source_file.absolute_path.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            code_c = 0
            comment_c = 0
            blank_c = 0

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_c += 1
                elif stripped.startswith(("#", "//", "/*", "*", "'''", '"""')):
                    comment_c += 1
                else:
                    code_c += 1

            return code_c, comment_c, blank_c
        except Exception:
            return source_file.line_count, 0, 0

    def _extract_ast_metrics(
        self, root_node: tree_sitter.Node, file_path: str
    ) -> Tuple[List[FunctionMetrics], List[ClassMetrics]]:
        """Traverse AST to compute FunctionMetrics and ClassMetrics."""
        funcs: List[FunctionMetrics] = []
        classes: List[ClassMetrics] = []

        def _traverse(node: tree_sitter.Node) -> None:
            if node.type in {"function_definition", "function_declaration", "method_definition"}:
                name = "<anonymous>"
                for child in node.children:
                    if child.type in {"identifier", "property_identifier"}:
                        name = child.text.decode("utf-8", errors="ignore")
                        break

                start_l = node.start_point[0] + 1
                end_l = node.end_point[0] + 1
                loc = (end_l - start_l) + 1
                cc = self.calculator.compute_node_complexity(node)
                nesting = self.calculator.compute_max_nesting_depth(node)
                params, returns = self.calculator.extract_function_details(node)
                mi = self.calculator.calculate_maintainability_index(loc, cc)

                funcs.append(
                    FunctionMetrics(
                        name=name,
                        file_path=file_path,
                        start_line=start_l,
                        end_line=end_l,
                        lines_of_code=loc,
                        cyclomatic_complexity=cc,
                        max_nesting_depth=nesting,
                        parameter_count=params,
                        return_count=returns,
                        maintainability_index=mi,
                    )
                )

            elif node.type in {"class_definition", "class_declaration"}:
                c_name = "<anonymous>"
                for child in node.children:
                    if child.type == "identifier":
                        c_name = child.text.decode("utf-8", errors="ignore")
                        break

                start_l = node.start_point[0] + 1
                end_l = node.end_point[0] + 1
                loc = (end_l - start_l) + 1

                # Count methods inside class
                method_count = 0
                total_c_comp = 0
                for child in node.children:
                    if child.type in {"block", "class_body"}:
                        for body_child in child.children:
                            if body_child.type in {"function_definition", "method_definition"}:
                                method_count += 1
                                total_c_comp += self.calculator.compute_node_complexity(body_child)

                avg_m_comp = round(total_c_comp / max(1, method_count), 2)
                classes.append(
                    ClassMetrics(
                        name=c_name,
                        file_path=file_path,
                        start_line=start_l,
                        end_line=end_l,
                        lines_of_code=loc,
                        method_count=method_count,
                        total_complexity=total_c_comp,
                        average_method_complexity=avg_m_comp,
                    )
                )

            for child in node.children:
                _traverse(child)

        _traverse(root_node)
        return funcs, classes
