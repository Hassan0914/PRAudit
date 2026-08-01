"""Data models for targeted context assembly and token budgeting."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ContextSection:
    """Represents a section in the assembled LLM prompt context."""

    title: str
    content: str
    estimated_tokens: int = 0
    priority: int = 1  # 1 = Highest, 5 = Lowest


@dataclass
class AssembledContext:
    """Container for assembled, token-budgeted prompt context."""

    pr_id: str
    sections: List[ContextSection] = field(default_factory=list)
    total_estimated_tokens: int = 0
    token_budget: int = 16000
    is_truncated: bool = False
    assembled_text: str = ""
