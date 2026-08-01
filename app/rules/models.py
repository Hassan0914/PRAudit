"""Data models for custom rule management, rule packs, and organization overrides."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RuleSeverity(str, Enum):
    """Severity levels for custom rules."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RuleCategory(str, Enum):
    """Categories for custom review rules."""

    COMPLEXITY = "COMPLEXITY"
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    MAINTAINABILITY = "MAINTAINABILITY"
    STYLE = "STYLE"


@dataclass
class RuleVersion:
    """Version specification for a rule."""

    version: str
    created_at: str = ""
    author: str = "admin"


@dataclass
class Rule:
    """Represents a review rule definition."""

    rule_id: str
    name: str
    description: str
    category: RuleCategory
    severity: RuleSeverity
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    version: RuleVersion = field(default_factory=lambda: RuleVersion("1.0.0"))


@dataclass
class RulePack:
    """Container for a group of rules (RulePack)."""

    pack_id: str
    name: str
    description: str
    rules: List[Rule] = field(default_factory=list)
