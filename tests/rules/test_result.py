import pytest

from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_rule_result_stores_evaluation_result():
    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
    )

    assert result.rule_id == "R001"
    assert result.rule_name == "Revenue growth deterioration"
    assert result.category == "revenue"
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == -0.15
    assert result.threshold == -0.10


def test_rule_result_is_immutable():
    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
    )

    with pytest.raises(AttributeError):
        result.status = RuleStatus.NOT_TRIGGERED
