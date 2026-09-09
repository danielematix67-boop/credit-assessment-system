import pytest

from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
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
        indicator="Test indicator",
        direction=SeverityDirection.HIGHER_IS_WORSE,
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
        "indicator": "Test indicator",
        "direction": SeverityDirection.HIGHER_IS_WORSE,
    }

    for field, expected_value in expected_values.items():
        assert getattr(rule_result, field) == expected_value


def test_rule_result_is_triggered(rule_result):
    assert rule_result.is_triggered is True


def test_rule_result_is_not_triggered_when_status_is_not_triggered():
    result = RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        status=RuleStatus.NOT_TRIGGERED,
        value=1.0,
        threshold=2.0,
        severity=RuleSeverity.MEDIUM,
        indicator="Test indicator",
        direction=SeverityDirection.HIGHER_IS_WORSE,
    )

    assert result.is_triggered is False


def test_rule_result_preserves_lower_is_worse_direction():
    result = RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=-0.10,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
        indicator="Revenue growth",
        direction=SeverityDirection.LOWER_IS_WORSE,
    )

    assert result.indicator == "Revenue growth"
    assert result.direction == SeverityDirection.LOWER_IS_WORSE


def test_rule_result_is_immutable(rule_result):
    with pytest.raises(AttributeError):
        rule_result.status = RuleStatus.NOT_TRIGGERED
