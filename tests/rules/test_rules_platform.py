"""Unit tests for Phase 22: Rule Management Platform."""

from app.rules.engine import RuleManagementService
from app.rules.loader import RuleLoader
from app.rules.models import Rule, RuleCategory, RuleSeverity


def test_rule_loader_and_management() -> None:
    loader = RuleLoader()
    rule_dict = {
        "rule_id": "CUSTOM-001",
        "name": "Custom Naming Rule",
        "description": "Enforce camelCase naming.",
        "category": "STYLE",
        "severity": "LOW",
    }
    rule = loader.load_from_dict(rule_dict)

    service = RuleManagementService(loader=loader)
    service.register_rule(rule)

    active = service.get_active_rules()
    assert len(active) == 1
    assert active[0].rule_id == "CUSTOM-001"

    service.disable_rule("CUSTOM-001")
    assert len(service.get_active_rules()) == 0

    service.set_repository_override("SpecialRepo", "CUSTOM-001", True)
    assert len(service.get_active_rules("SpecialRepo")) == 1
