"""Validator verifying custom rule schema compliance."""

from typing import Any, Dict
from app.core.exceptions import PRAuditError
from app.rules.models import Rule, RuleCategory, RuleSeverity


class RuleValidator:
    """Validator verifying rule configuration schema."""

    def validate_rule_dict(self, data: Dict[str, Any]) -> bool:
        """Validate rule dictionary format.

        Args:
            data: Rule configuration dictionary.

        Returns:
            True if valid, raises PRAuditError if invalid.
        """
        required_fields = ["rule_id", "name", "description", "category", "severity"]
        for field_name in required_fields:
            if field_name not in data:
                raise PRAuditError(f"Missing required field '{field_name}' in rule definition.")

        if not isinstance(data["rule_id"], str) or not data["rule_id"].strip():
            raise PRAuditError("Invalid 'rule_id': must be non-empty string.")

        try:
            RuleCategory(data["category"].upper())
        except ValueError as exc:
            raise PRAuditError(f"Invalid rule category '{data['category']}'.") from exc

        try:
            RuleSeverity(data["severity"].upper())
        except ValueError as exc:
            raise PRAuditError(f"Invalid rule severity '{data['severity']}'.") from exc

        return True
