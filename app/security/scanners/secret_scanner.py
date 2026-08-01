"""Secret and credential scanner plugin."""

import hashlib
import re
import time
from pathlib import Path
from typing import List, Tuple

from app.core.logging import setup_logger
from app.parsing.models import ParseResult
from app.repository.models import SourceFile
from app.security.models import (
    ConfidenceLevel,
    ScannerResult,
    SecurityFinding,
    VulnerabilitySeverity,
)
from app.security.scanners.base import BaseSecurityScanner

logger = setup_logger("security.secret")


class SecretScanner(BaseSecurityScanner):
    """Deterministic secret scanner detecting exposed keys, tokens, and credentials."""

    SECRET_PATTERNS: List[Tuple[str, str, re.Pattern, VulnerabilitySeverity, str]] = [
        (
            "SEC-AWS-KEY",
            "AWS Access Key ID",
            re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
            VulnerabilitySeverity.CRITICAL,
            "CWE-798",
        ),
        (
            "SEC-RSA-KEY",
            "RSA / Private Key Block",
            re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            VulnerabilitySeverity.CRITICAL,
            "CWE-312",
        ),
        (
            "SEC-HARDCODED-PASS",
            "Hardcoded Password Assignment",
            re.compile(r"""(?i)(?:password|passwd|pwd|secret|api_key|token)\s*[:=]\s*["']([^"']{8,})["']"""),
            VulnerabilitySeverity.HIGH,
            "CWE-798",
        ),
    ]

    @property
    def name(self) -> str:
        return "secret_scanner"

    def scan(
        self, repo_path: Path, source_files: List[SourceFile], parse_results: List[ParseResult]
    ) -> ScannerResult:
        start_time = time.perf_counter()
        findings: List[SecurityFinding] = []

        for sf in source_files:
            if not sf.is_supported:
                continue

            try:
                text = sf.absolute_path.read_text(encoding="utf-8", errors="ignore")
                lines = text.splitlines()

                for line_idx, line in enumerate(lines, start=1):
                    for rule_id, title, pattern, severity, cwe in self.SECRET_PATTERNS:
                        match = pattern.search(line)
                        if match:
                            snippet = line.strip()
                            f_id = hashlib.sha256(f"secret:{sf.relative_path}:{line_idx}:{rule_id}".encode()).hexdigest()[:16]

                            findings.append(
                                SecurityFinding(
                                    finding_id=f_id,
                                    vulnerability_id=rule_id,
                                    scanner_name=self.name,
                                    file_path=sf.relative_path,
                                    line=line_idx,
                                    severity=severity,
                                    confidence=ConfidenceLevel.HIGH,
                                    message=f"Possible exposed secret detected: {title}",
                                    cwe_id=cwe,
                                    recommendation="Remove hardcoded credentials and store in environment variables or secret manager.",
                                    snippet=snippet[:60],
                                )
                            )
            except Exception as exc:
                logger.warning("Failed to scan secrets in file %s: %s", sf.relative_path, exc)

        duration = (time.perf_counter() - start_time) * 1000.0
        return ScannerResult(
            scanner_name=self.name, is_success=True, execution_duration_ms=duration, findings=findings
        )
