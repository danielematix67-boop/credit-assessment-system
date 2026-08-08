from src.rules.registry import get_default_rules


def test_default_rules_registry():
    rules = get_default_rules()

    assert len(rules) == 4

    assert rules[0].rule_id == "R001"
    assert rules[1].rule_id == "R002"
    assert rules[2].rule_id == "R003"
    assert rules[3].rule_id == "R004"