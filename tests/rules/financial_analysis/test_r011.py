from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r011 import TradePayablesIncreaseRule

CONFIG = RuleConfig(
    rule_id="R011",
    rule_name="Increase in trade payables vs historical average",
    category="working_capital",
    threshold=0.10,
    severity=RuleSeverity.MEDIUM,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=0.10, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=0.20, severity=RuleSeverity.HIGH),
    ),
    input_field="trade_payables_current",
    trigger_operator="GT",
)


def position(current, one_year, two_years, three_years, four_years):
    return CreditPosition(
        position_id="TEST_POSITION",
        trade_payables_current=current,
        trade_payables_1y_ago=one_year,
        trade_payables_2y_ago=two_years,
        trade_payables_3y_ago=three_years,
        trade_payables_4y_ago=four_years,
    )


def test_r011_triggers_medium_for_material_acceleration():
    result = TradePayablesIncreaseRule(CONFIG).evaluate(
        position(127, 100, 90, 80, 70)
    )
    assert result.value is not None
    assert 0.10 < result.value < 0.20
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r011_triggers_high_for_large_acceleration():
    result = TradePayablesIncreaseRule(CONFIG).evaluate(
        position(150, 100, 90, 80, 70)
    )
    assert result.value is not None
    assert result.value > 0.20
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_r011_does_not_trigger_without_positive_current_growth():
    result = TradePayablesIncreaseRule(CONFIG).evaluate(
        position(90, 100, 80, 90, 100)
    )
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r011_does_not_trigger_when_growth_is_in_line_with_history():
    result = TradePayablesIncreaseRule(CONFIG).evaluate(
        position(110, 100, 90, 80, 70)
    )
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r011_is_not_evaluable_for_missing_or_invalid_inputs():
    rule = TradePayablesIncreaseRule(CONFIG)
    for values in (
        (None, 100, 90, 80, 70),
        (110, None, 90, 80, 70),
        (110, 100, None, 80, 70),
        (110, 100, 90, None, 70),
        (110, 100, 90, 80, None),
        (110, 0, 90, 80, 70),
        (110, 100, 0, 80, 70),
        (110, 100, 90, -1, 70),
    ):
        result = rule.evaluate(position(*values))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
