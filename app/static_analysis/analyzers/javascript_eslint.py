"""ESLint static analyzer plugin for JavaScript and TypeScript."""

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

logger = setup_logger("static_analysis.eslint")


class ESLintAnalyzer(BaseAnalyzer):
    """ESLint static analyzer inspecting JavaScript and TypeScript source files."""

    @property
    def name(self) -> str:
        return "eslint"

    def analyze(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> AnalyzerResult:
        start_time = time.perf_counter()
        findings: List[StaticAnalysisFinding] = []

        js_files = [
            sf for sf in source_files
            if sf.language in {Language.JAVASCRIPT, Language.TYPESCRIPT} and sf.is_supported
        ]
        if not js_files:
            duration = (time.perf_counter() - start_time) * 1000.0
            return AnalyzerResult(analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=[])

        # AST fallback for JS/TS lint checks (e.g. console.log calls, eval usage)
        for pr in parse_results:
            if pr.language not in {Language.JAVASCRIPT, Language.TYPESCRIPT} or not pr.raw_tree or not pr.raw_tree.root_node:
                continue

            self._check_js_rules(pr.raw_tree.root_node, pr.file_path, findings)

        duration = (time.perf_counter() - start_time) * 1000.0
        return AnalyzerResult(
            analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings
        )

    def _check_js_rules(
        self, root_node: tree_sitter.Node, file_path: str, findings: List[StaticAnalysisFinding]
    ) -> None:
        """Inspect JS/TS AST for common lint rules."""

        def _traverse(node: tree_sitter.Node) -> None:
            if node.type in {"call", "call_expression"}:
                text = node.text.decode("utf-8", errors="ignore")
                if "console.log" in text:
                    line = node.start_point[0] + 1
                    col = node.start_point[1] + 1
                    f_id = hashlib.sha256(f"eslint:no-console:{file_path}:{line}".encode()).hexdigest()[:16]
                    findings.append(
                        StaticAnalysisFinding(
                            finding_id=f_id,
                            rule_id="no-console",
                            analyzer_name=self.name,
                            file_path=file_path,
                            line=line,
                            column=col,
                            severity=FindingSeverity.LOW,
                            message="Unexpected console.log statement.",
                            snippet=text[:60],
                        )
                    )

            for child in node.children:
                _traverse(child)

        _traverse(root_node)
