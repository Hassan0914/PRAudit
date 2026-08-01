"""Unit tests for Phase 10: Security Analysis Engine."""

from pathlib import Path
from app.core.types import Language
from app.parsing.service import ParsingEngine
from app.repository.discovery import RepositoryDiscoveryEngine
from app.security.models import VulnerabilitySeverity
from app.security.registry import SecurityEngine


def test_security_engine_execution(temp_repo: Path) -> None:
    """Test running security scanners across repository files."""
    discovery = RepositoryDiscoveryEngine()
    parser = ParsingEngine()
    sec_engine = SecurityEngine()

    metadata, files, stats = discovery.discover(temp_repo)
    parse_results = [parser.parse_file(sf) for sf in files if sf.is_supported]

    report = sec_engine.run_security_scan(temp_repo, files, parse_results)

    assert report is not None
    assert len(report.scanner_results) == 2  # Bandit, SecretScanner
    assert all(res.is_success for res in report.scanner_results)


def test_secret_scanner_detection(tmp_path: Path) -> None:
    """Test SecretScanner identifies exposed AWS keys and hardcoded passwords."""
    sec_file = tmp_path / "secrets.py"
    sec_file.write_text(
        'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
        'DB_PASS = "super_secret_password_123"\n'
    )

    discovery = RepositoryDiscoveryEngine()
    sec_engine = SecurityEngine()

    metadata, files, stats = discovery.discover(tmp_path)
    report = sec_engine.run_security_scan(tmp_path, files, [])

    assert report.total_vulnerabilities >= 1
    rule_ids = [v.vulnerability_id for v in report.findings]
    assert "SEC-AWS-KEY" in rule_ids or "SEC-HARDCODED-PASS" in rule_ids
