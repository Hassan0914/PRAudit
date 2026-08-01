"""MyPy type-checker static analyzer plugin for Python."""

import hashlib
import time
from pathlib import Path
from typing import List
import tree_sitter

from app.core.logging import setup_logger
from app.core.types import Language
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.static_analysis.analyzers.base import BaseAnalyzer
from app.static_analysis.models import (
    AnalyzerResult,
    FindingSeverity,
    StaticAnalysisFinding,
)

logger = setup_logger("static_analysis.mypy")


class MyPyAnalyzer(BaseAnalyzer):
    """MyPy static analyzer inspecting Python type safety."""

    @property
    def name(self) -> str:
        return "mypy"

    def analyze(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> AnalyzerResult:
        start_time = time.perf_counter()
        findings: List[StaticAnalysisFinding] = []

        py_files = [sf for sf in source_files if sf.language == Language.PYTHON and sf.is_supported]
        if not py_files:
            duration = (time.perf_counter() - start_time) * 1000.0
            return AnalyzerResult(analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=[])

        # AST fallback for missing type annotations
        for pr in parse_results:
            if pr.language != Language.PYTHON or not pr.raw_tree or not pr.raw_tree.root_node:
                continue

            self._check_untyped_functions(pr.raw_tree.root_node, pr.file_path, findings)

        duration = (time.perf_counter() - start_time) * 1000.0
        return AnalyzerResult(
            analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings
        )

    def _check_untyped_functions(
        self, root_node: tree_sitter.Node, file_path: str, findings: List[StaticAnalysisFinding]
    ) -> None:
        """Inspect functions for missing type annotations."""

        def _traverse(node: tree_sitter.Node) -> None:
            if node.type == "function_definition":
                func_name = "<anonymous>"
                has_return_type = False

                for child in node.children:
                    if child.type == "identifier":
                        func_name = child.text.decode("utf-8", errors="ignore")
                    elif child.type == "type":
                        has_return_type = True

                if not has_return_type and not func_name.startswith("__"):
                    line = node.start_point[0] + 1
                    col = node.start_point[1] + 1
                    f_id = hashlib.sha256(f"mypy:{file_path}:{line}:{func_name}".encode()).hexdigest()[:16]

                    findings.append(
                        StaticAnalysisFinding(
                            finding_id=f_id,
                            rule_id="no-untyped-def",
                            analyzer_name=self.name,
                            file_path=file_path,
                            line=line,
                            column=col,
                            severity=FindingSeverity.LOW,
                            message=f"Function '{func_name}' is missing explicit return type annotation.",
                        )
                    )

            for child in node.children:
                _traverse(child)

        _traverse(root_node)
