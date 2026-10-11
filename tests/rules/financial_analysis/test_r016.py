from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r016 import IntangibleAssetsConcentrationRule

CONFIG = RuleConfig(
    rule_id="R016",
    rule_name="Intangible assets concentration in total assets",
    category="asset_quality",
    threshold=0.15,
    severity=RuleSeverity.MEDIUM,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=0.15, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=0.25, severity=RuleSeverity.HIGH),
    ),
    input_field="intangible_assets",
    trigger_operator="GT",
)


def position(intangible_assets, total_assets):
    return CreditPosition(
        position_id="TEST_POSITION",
        intangible_assets=intangible_assets,
        total_assets=total_assets,
    )


def test_r016_does_not_trigger_below_threshold():
    result = IntangibleAssetsConcentrationRule(CONFIG).evaluate(position(10, 100))
    assert result.value == 0.10
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r016_triggers_medium_above_fifteen_percent():
    result = IntangibleAssetsConcentrationRule(CONFIG).evaluate(position(20, 100))
    assert result.value == 0.20
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r016_triggers_high_above_twenty_five_percent():
    result = IntangibleAssetsConcentrationRule(CONFIG).evaluate(position(30, 100))
    assert result.value == 0.30
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH
    assert "not evidence of improper accounting" in result.reason


def test_r016_fifteen_percent_boundary_is_exclusive():
    result = IntangibleAssetsConcentrationRule(CONFIG).evaluate(position(15, 100))
    assert result.value == 0.15
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r016_is_not_evaluable_for_missing_or_invalid_inputs():
    rule = IntangibleAssetsConcentrationRule(CONFIG)
    for intangible_assets, total_assets in (
        (None, 100),
        (10, None),
        (-1, 100),
        (10, 0),
        (10, -1),
        (101, 100),
        (float("nan"), 100),
        (10, float("inf")),
        (True, 100),
    ):
        result = rule.evaluate(position(intangible_assets, total_assets))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
