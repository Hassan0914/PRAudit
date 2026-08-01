"""Ruff static analyzer plugin for Python code quality analysis."""

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import List

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

logger = setup_logger("static_analysis.ruff")


class RuffAnalyzer(BaseAnalyzer):
    """Ruff static analyzer inspecting Python source code."""

    @property
    def name(self) -> str:
        return "ruff"

    def analyze(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> AnalyzerResult:
        start_time = time.perf_counter()
        findings: List[StaticAnalysisFinding] = []

        py_files = [sf for sf in source_files if sf.language == Language.PYTHON and sf.is_supported]
        if not py_files:
            duration = (time.perf_counter() - start_time) * 1000.0
            return AnalyzerResult(analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=[])

        # Attempt Ruff CLI invocation if available
        try:
            cmd = ["ruff", "check", "--output-format=json", str(repo_path)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if proc.returncode in {0, 1} and proc.stdout.strip().startswith("["):
                raw_json = json.loads(proc.stdout)
                for item in raw_json:
                    rel_path = item.get("filename", "")
                    if rel_path.startswith(str(repo_path)):
                        rel_path = rel_path[len(str(repo_path)) :].lstrip("/\\")

                    line = item.get("location", {}).get("row", 1)
                    col = item.get("location", {}).get("column", 1)
                    code = item.get("code", "E999")
                    msg = item.get("message", "Lint finding")

                    f_id = hashlib.sha256(f"ruff:{rel_path}:{line}:{code}".encode()).hexdigest()[:16]
                    findings.append(
                        StaticAnalysisFinding(
                            finding_id=f_id,
                            rule_id=code,
                            analyzer_name=self.name,
                            file_path=rel_path,
                            line=line,
                            column=col,
                            severity=FindingSeverity.MEDIUM,
                            message=msg,
                        )
                    )

                duration = (time.perf_counter() - start_time) * 1000.0
                return AnalyzerResult(analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings)
        except Exception as exc:
            logger.debug("Ruff CLI binary not executed (%s). Running deterministic AST lint analyzer fallback.", exc)

        # Fallback deterministic AST lint inspection
        for pr in parse_results:
            if pr.language != Language.PYTHON or not pr.raw_tree or not pr.raw_tree.root_node:
                continue

            for err in pr.errors:
                f_id = hashlib.sha256(f"ruff_ast:{pr.file_path}:{err.line}:{err.column}".encode()).hexdigest()[:16]
                findings.append(
                    StaticAnalysisFinding(
                        finding_id=f_id,
                        rule_id="E999",
                        analyzer_name=self.name,
                        file_path=pr.file_path,
                        line=err.line,
                        column=err.column,
                        severity=FindingSeverity.HIGH,
                        message=f"Syntax Error: {err.message}",
                        snippet=err.text,
                    )
                )

        duration = (time.perf_counter() - start_time) * 1000.0
        return AnalyzerResult(
            analyzer_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings
        )
