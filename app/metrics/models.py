"""Data models for repository quality and complexity metrics."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FunctionMetrics:
    """Quality and complexity metrics for a function or method."""

    name: str
    file_path: str
    start_line: int
    end_line: int
    lines_of_code: int
    cyclomatic_complexity: int
    max_nesting_depth: int
    parameter_count: int
    return_count: int
    maintainability_index: float


@dataclass
class ClassMetrics:
    """Quality and complexity metrics for a class."""

    name: str
    file_path: str
    start_line: int
    end_line: int
    lines_of_code: int
    method_count: int
    total_complexity: int
    average_method_complexity: float


@dataclass
class FileMetrics:
    """Quality and complexity metrics for a source file."""

    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    total_complexity: int
    average_function_complexity: float
    max_cyclomatic_complexity: int
    maintainability_index: float
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: List[ClassMetrics] = field(default_factory=list)


@dataclass
class RepositoryMetrics:
    """Aggregate quality and complexity metrics for an entire repository."""

    total_files: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    total_comment_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    average_cyclomatic_complexity: float = 0.0
    average_maintainability_index: float = 0.0
    file_metrics: Dict[str, FileMetrics] = field(default_factory=dict)
