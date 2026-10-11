from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r014 import AverageCollectionDaysIncreaseRule

CONFIG = RuleConfig(
    rule_id="R014",
    rule_name="Increase in average collection days vs historical average",
    category="working_capital",
    threshold=10.0,
    severity=RuleSeverity.MEDIUM,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=10.0, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=20.0, severity=RuleSeverity.HIGH),
    ),
    input_field="avg_collection_days_current",
    trigger_operator="GT",
)


def position(current, one_year, two_years, three_years, four_years):
    return CreditPosition(
        position_id="TEST_POSITION",
        avg_collection_days_current=current,
        avg_collection_days_1y_ago=one_year,
        avg_collection_days_2y_ago=two_years,
        avg_collection_days_3y_ago=three_years,
        avg_collection_days_4y_ago=four_years,
    )


def test_r014_triggers_medium_when_current_days_exceed_historical_average():
    result = AverageCollectionDaysIncreaseRule(CONFIG).evaluate(
        position(115, 100, 100, 100, 100)
    )
    assert result.value == 15.0
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r014_triggers_high_when_current_days_materially_exceed_historical_average():
    result = AverageCollectionDaysIncreaseRule(CONFIG).evaluate(
        position(125, 100, 100, 100, 100)
    )
    assert result.value == 25.0
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_r014_does_not_trigger_when_current_days_are_close_to_history():
    result = AverageCollectionDaysIncreaseRule(CONFIG).evaluate(
        position(105, 100, 100, 100, 100)
    )
    assert result.value == 5.0
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r014_does_not_trigger_when_current_days_are_below_historical_average():
    result = AverageCollectionDaysIncreaseRule(CONFIG).evaluate(
        position(80, 100, 90, 80, 70)
    )
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r014_ten_day_boundary_is_exclusive():
    result = AverageCollectionDaysIncreaseRule(CONFIG).evaluate(
        position(110, 100, 100, 100, 100)
    )
    assert result.value == 10.0
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r014_is_not_evaluable_for_missing_or_invalid_inputs():
    rule = AverageCollectionDaysIncreaseRule(CONFIG)
    for values in (
        (None, 105, 100, 90, 80),
        (130, None, 100, 90, 80),
        (130, 105, None, 90, 80),
        (130, 105, 100, None, 80),
        (130, 105, 100, 90, None),
        (130, 105, 100, -1, 80),
        (130, 105, 100, float("nan"), 80),
        (130, 105, 100, True, 80),
    ):
        result = rule.evaluate(position(*values))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
