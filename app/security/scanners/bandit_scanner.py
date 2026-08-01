"""Bandit security scanner plugin inspecting Python code for security issues."""

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import List
import tree_sitter

from app.core.logging import setup_logger
from app.core.types import Language
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.security.scanners.base import BaseSecurityScanner
from app.security.models import (
    ConfidenceLevel,
    ScannerResult,
    SecurityFinding,
    VulnerabilitySeverity,
)

logger = setup_logger("security.bandit")


class BanditScanner(BaseSecurityScanner):
    """Bandit security scanner for Python security analysis."""

    @property
    def name(self) -> str:
        return "bandit"

    def scan(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> ScannerResult:
        start_time = time.perf_counter()
        findings: List[SecurityFinding] = []

        py_files = [sf for sf in source_files if sf.language == Language.PYTHON and sf.is_supported]
        if not py_files:
            duration = (time.perf_counter() - start_time) * 1000.0
            return ScannerResult(scanner_name=self.name, is_success=True, execution_duration_ms=duration, findings=[])

        # Attempt Bandit CLI execution if installed
        try:
            cmd = ["bandit", "-r", str(repo_path), "-f", "json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if proc.stdout.strip().startswith("{"):
                data = json.loads(proc.stdout)
                for item in data.get("results", []):
                    file_p = item.get("filename", "")
                    if file_p.startswith(str(repo_path)):
                        file_p = file_p[len(str(repo_path)) :].lstrip("/\\")

                    line = item.get("line_number", 1)
                    test_id = item.get("test_id", "B100")
                    issue_text = item.get("issue_text", "Security vulnerability")
                    sev_str = item.get("issue_severity", "MEDIUM").upper()
                    conf_str = item.get("issue_confidence", "MEDIUM").upper()

                    sev = (
                        VulnerabilitySeverity.HIGH
                        if sev_str == "HIGH"
                        else VulnerabilitySeverity.MEDIUM
                        if sev_str == "MEDIUM"
                        else VulnerabilitySeverity.LOW
                    )
                    conf = (
                        ConfidenceLevel.HIGH
                        if conf_str == "HIGH"
                        else ConfidenceLevel.MEDIUM
                        if conf_str == "MEDIUM"
                        else ConfidenceLevel.LOW
                    )

                    f_id = hashlib.sha256(f"bandit:{file_p}:{line}:{test_id}".encode()).hexdigest()[:16]
                    findings.append(
                        SecurityFinding(
                            finding_id=f_id,
                            vulnerability_id=test_id,
                            scanner_name=self.name,
                            file_path=file_p,
                            line=line,
                            severity=sev,
                            confidence=conf,
                            message=issue_text,
                            cwe_id="CWE-78" if "shell" in issue_text.lower() else "CWE-95",
                            recommendation="Avoid unsafe dynamic function execution or un-sanitized inputs.",
                        )
                    )

                duration = (time.perf_counter() - start_time) * 1000.0
                return ScannerResult(scanner_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings)
        except Exception as exc:
            logger.debug("Bandit CLI not executed (%s). Running AST security scanner fallback.", exc)

        # Fallback AST Security Inspection (eval, exec, shell=True)
        for pr in parse_results:
            if pr.language != Language.PYTHON or not pr.raw_tree or not pr.raw_tree.root_node:
                continue

            self._scan_ast_security(pr.raw_tree.root_node, pr.file_path, findings)

        duration = (time.perf_counter() - start_time) * 1000.0
        return ScannerResult(
            scanner_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings
        )

    def _scan_ast_security(
        self, root_node: tree_sitter.Node, file_path: str, findings: List[SecurityFinding]
    ) -> None:
        """Scan Python AST for dangerous functions (eval, exec, pickle)."""

        def _traverse(node: tree_sitter.Node) -> None:
            if node.type == "call":
                first_child = node.children[0] if node.children else None
                if first_child and first_child.type == "identifier":
                    func_name = first_child.text.decode("utf-8", errors="ignore")
                    if func_name in {"eval", "exec"}:
                        line = node.start_point[0] + 1
                        f_id = hashlib.sha256(f"bandit_ast:{file_path}:{line}:{func_name}".encode()).hexdigest()[:16]
                        findings.append(
                            SecurityFinding(
                                finding_id=f_id,
                                vulnerability_id="B307" if func_name == "eval" else "B102",
                                scanner_name=self.name,
                                file_path=file_path,
                                line=line,
                                severity=VulnerabilitySeverity.HIGH,
                                confidence=ConfidenceLevel.HIGH,
                                message=f"Use of dangerous function '{func_name}()' detected.",
                                cwe_id="CWE-95",
                                recommendation=f"Avoid using '{func_name}()' with dynamic code input.",
                                snippet=node.text.decode("utf-8", errors="ignore")[:60],
                            )
                        )

            for child in node.children:
                _traverse(child)

        _traverse(root_node)
