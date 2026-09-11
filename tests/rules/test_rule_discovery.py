from src.rules.base.rule import Rule
from src.rules.discovery import discover_rules


def test_discover_rules_loads_registered_rules():
    discover_rules()

    assert Rule._registry
    assert all(
        isinstance(rule_id, str) and rule_id and issubclass(rule_class, Rule)
        for rule_id, rule_class in Rule._registry.items()
    )


def test_discover_rules_registers_rules_with_unique_ids():
    discover_rules()

    rule_ids = list(Rule._registry)

    assert len(rule_ids) == len(set(rule_ids))


def test_discover_rules_registers_r004_leverage_rule():
    discover_rules()

    assert "R004" in Rule._registry


def test_discover_rules_is_idempotent():
    discover_rules()

    first_registry = Rule._registry.copy()

    discover_rules()

    assert Rule._registry == first_registry
