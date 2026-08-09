from src.rules.base.severity import RuleSeverity


def test_rule_severity_contains_expected_levels():
    assert RuleSeverity.LOW.value == "LOW"
    assert RuleSeverity.MEDIUM.value == "MEDIUM"
    assert RuleSeverity.HIGH.value == "HIGH"


def test_rule_severity_is_string_based():
    assert isinstance(RuleSeverity.LOW, str)
    assert isinstance(RuleSeverity.MEDIUM, str)
    assert isinstance(RuleSeverity.HIGH, str)

