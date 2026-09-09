import pytest

from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@pytest.fixture
def rule_result():
    return RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )


def test_rule_result_stores_provided_data(rule_result):
    expected_values = {
        "rule_id": "TEST_RULE",
        "rule_name": "Test rule",
        "category": "test",
        "status": RuleStatus.TRIGGERED,
        "value": 1.0,
        "threshold": 0.0,
        "severity": RuleSeverity.MEDIUM,
    }

    for field, expected_value in expected_values.items():
        assert getattr(rule_result, field) == expected_value


def test_rule_result_is_immutable(rule_result):
    with pytest.raises(AttributeError):
        rule_result.status = RuleStatus.NOT_TRIGGERED
