from src.rules.base.severity import RuleSeverity


def test_rule_severity_contains_expected_levels():
    expected_levels = {
        severity.name
        for severity in RuleSeverity
    }

    assert expected_levels == {
        severity.value
        for severity in RuleSeverity
    }


def test_rule_severity_members_are_string_based():
    assert all(
        isinstance(severity, str)
        for severity in RuleSeverity
    )


def test_rule_severity_values_are_unique():
    values = [
        severity.value
        for severity in RuleSeverity
    ]

    assert len(values) == len(set(values))