"""Loader loading custom rules from JSON, YAML, and Python plugin dictionaries."""

import json
from typing import Any, Dict, List, Optional
from app.core.logging import setup_logger
from app.rules.models import Rule, RuleCategory, RuleSeverity, RuleVersion
from app.rules.validator import RuleValidator

logger = setup_logger("rules.loader")


class RuleLoader:
    """Loader loading rules from structured definitions."""

    def __init__(self, validator: Optional[RuleValidator] = None) -> None:
        self.validator = validator or RuleValidator()

    def load_from_dict(self, data: Dict[str, Any]) -> Rule:
        """Load a Rule object from a dictionary structure."""
        self.validator.validate_rule_dict(data)
        return Rule(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["description"],
            category=RuleCategory(data["category"].upper()),
            severity=RuleSeverity(data["severity"].upper()),
            enabled=data.get("enabled", True),
            parameters=data.get("parameters", {}),
            version=RuleVersion(data.get("version", "1.0.0")),
        )

    def load_from_json(self, json_str: str) -> List[Rule]:
        """Load rules from JSON string."""
        raw_list = json.loads(json_str)
        if isinstance(raw_list, dict):
            raw_list = [raw_list]
        return [self.load_from_dict(item) for item in raw_list]
