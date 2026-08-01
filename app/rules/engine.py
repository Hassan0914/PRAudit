"""Rule Management Service managing active rules, rule packs, and repository overrides."""

from typing import Dict, List, Optional
from app.core.logging import setup_logger
from app.rules.loader import RuleLoader
from app.rules.models import Rule, RuleCategory, RulePack, RuleSeverity

logger = setup_logger("rules.engine")


class RuleManagementService:
    """Service providing rule registry management, toggling, and repository overrides."""

    def __init__(self, loader: Optional[RuleLoader] = None) -> None:
        self.loader = loader or RuleLoader()
        self._rules: Dict[str, Rule] = {}
        self._repo_overrides: Dict[str, Dict[str, bool]] = {}  # repo_name -> {rule_id: enabled}

    def register_rule(self, rule: Rule) -> None:
        """Register or update a rule definition."""
        self._rules[rule.rule_id] = rule
        logger.info("Registered rule '%s' (%s, Severity: %s)", rule.rule_id, rule.name, rule.severity.value)

    def enable_rule(self, rule_id: str) -> None:
        """Enable a rule globally."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True

    def disable_rule(self, rule_id: str) -> None:
        """Disable a rule globally."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False

    def set_repository_override(self, repo_name: str, rule_id: str, enabled: bool) -> None:
        """Set a repository-specific rule toggle override."""
        if repo_name not in self._repo_overrides:
            self._repo_overrides[repo_name] = {}
        self._repo_overrides[repo_name][rule_id] = enabled
        logger.info("Set override for repo '%s', rule '%s': enabled=%s", repo_name, rule_id, enabled)

    def get_active_rules(self, repo_name: Optional[str] = None) -> List[Rule]:
        """Get all currently active rules for a given repository."""
        active: List[Rule] = []
        for r_id, rule in self._rules.items():
            is_enabled = rule.enabled
            if repo_name and repo_name in self._repo_overrides:
                if r_id in self._repo_overrides[repo_name]:
                    is_enabled = self._repo_overrides[repo_name][r_id]

            if is_enabled:
                active.append(rule)

        return active
