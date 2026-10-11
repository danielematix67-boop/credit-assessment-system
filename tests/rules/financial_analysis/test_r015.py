import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r015 import TradeReceivablesGrowthGapRule

CONFIG = RuleConfig(
    rule_id="R015",
    rule_name="Trade receivables growth exceeds revenue growth",
    category="working_capital",
    threshold=0.10,
    severity=RuleSeverity.MEDIUM,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=0.10, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=0.20, severity=RuleSeverity.HIGH),
    ),
    input_field="trade_receivables_current",
    trigger_operator="GT",
)


def position(receivables_current, receivables_prior, revenue_current, revenue_prior):
    return CreditPosition(
        position_id="TEST_POSITION",
        trade_receivables_current=receivables_current,
        trade_receivables_1y_ago=receivables_prior,
        revenue=revenue_current,
        revenue_1y_ago=revenue_prior,
    )


def test_r015_triggers_medium_when_receivables_growth_outpaces_revenue():
    # Receivables +30%; revenue +10%; gap +20 percentage points.
    result = TradeReceivablesGrowthGapRule(CONFIG).evaluate(
        position(130, 100, 110, 100)
    )
    assert result.value == pytest.approx(0.20)
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r015_triggers_high_for_large_growth_gap():
    # Receivables +50%; revenue +10%; gap +40 percentage points.
    result = TradeReceivablesGrowthGapRule(CONFIG).evaluate(
        position(150, 100, 110, 100)
    )
    assert result.value == pytest.approx(0.40)
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_r015_does_not_trigger_when_growth_gap_is_below_threshold():
    # Receivables +15%; revenue +10%; gap +5 percentage points.
    result = TradeReceivablesGrowthGapRule(CONFIG).evaluate(
        position(115, 100, 110, 100)
    )
    assert result.value == pytest.approx(0.05)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r015_ten_percentage_point_boundary_is_exclusive():
    result = TradeReceivablesGrowthGapRule(CONFIG).evaluate(
        position(120, 100, 110, 100)
    )
    assert result.value == pytest.approx(0.10)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r015_is_not_evaluable_for_missing_invalid_or_nonpositive_prior_inputs():
    rule = TradeReceivablesGrowthGapRule(CONFIG)
    for values in (
        (None, 100, 110, 100),
        (130, None, 110, 100),
        (130, 100, None, 100),
        (130, 100, 110, None),
        (130, 0, 110, 100),
        (130, 100, 110, 0),
        (-1, 100, 110, 100),
        (130, 100, float("nan"), 100),
        (130, 100, 110, float("inf")),
        (130, True, 110, 100),
    ):
        result = rule.evaluate(position(*values))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
