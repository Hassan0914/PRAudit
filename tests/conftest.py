"""Pytest configuration and test fixtures for PRAudit."""

import tempfile
from pathlib import Path
from typing import Generator
import pytest

from app.core.types import Language
from app.repository.models import SourceFile


@pytest.fixture
def temp_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory structure mimicking a git repository."""
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    # .git mock
    git_dir = repo_dir / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    refs_dir = git_dir / "refs" / "heads"
    refs_dir.mkdir(parents=True)
    (refs_dir / "main").write_text("1234567890abcdef1234567890abcdef12345678\n")

    # .gitignore
    (repo_dir / ".gitignore").write_text("*.log\nignore_me/\n")

    # Source files
    src_dir = repo_dir / "src"
    src_dir.mkdir()

    py_file = src_dir / "main.py"
    py_file.write_text(
        '"""Main module docstring."""\n\n'
        'import os\n\n'
        'GLOBAL_CONST = "hello"\n\n'
        'def add(a: int, b: int) -> int:\n'
        '    """Add two numbers."""\n'
        '    return a + b\n\n'
        'class Calculator:\n'
        '    """Calculator class."""\n'
        '    def multiply(self, x: int, y: int) -> int:\n'
        '        return x * y\n'
    )

    js_file = src_dir / "utils.js"
    js_file.write_text(
        'import fs from "fs";\n\n'
        'export function greet(name) {\n'
        '  return `Hello ${name}`;\n'
        '}\n\n'
        'export class Greeter {\n'
        '  sayHello() {\n'
        '    return "Hello";\n'
        '  }\n'
        '}\n'
    )

    # Ignored directory & files
    ignored_dir = repo_dir / "ignore_me"
    ignored_dir.mkdir()
    (ignored_dir / "temp.txt").write_text("ignored file")
    (repo_dir / "app.log").write_text("log content")

    # Malformed file
    malformed_file = src_dir / "bad.py"
    malformed_file.write_text("def broken_func(: def\n")

    yield repo_dir


@pytest.fixture
def sample_python_source(temp_repo: Path) -> SourceFile:
    """Fixture returning a SourceFile object for main.py."""
    abs_path = temp_repo / "src" / "main.py"
    return SourceFile(
        relative_path="src/main.py",
        absolute_path=abs_path,
        extension=".py",
        language=Language.PYTHON,
        size_bytes=abs_path.stat().st_size,
        line_count=len(abs_path.read_text().splitlines()),
        is_supported=True,
    )
