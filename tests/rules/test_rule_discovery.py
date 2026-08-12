from src.rules.base.rule import Rule
from src.rules.discovery import discover_rules


def test_discover_rules_loads_registered_rules():
    discover_rules()

    assert "R001" in Rule._registry
    assert "R002" in Rule._registry
    assert "R003" in Rule._registry
    assert "R004" in Rule._registry
    assert "R005" in Rule._registry
    assert "R006" in Rule._registry
    assert "R007" in Rule._registry


def test_discover_rules_is_idempotent():
    discover_rules()

    first_registry = Rule._registry.copy()

    discover_rules()

    assert Rule._registry == first_registry