from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r006 import EbitdaInventoryContributionRule

CONFIG = RuleConfig(
    rule_id="R006",
    rule_name="EBITDA inventory contribution",
    category="profitability",
    threshold=0.30,
    severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=0.30, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=0.50, severity=RuleSeverity.HIGH),
    ),
    input_fields=("change_in_finished_goods_inventory", "ebitda"),
    calculation="ratio",
    trigger_operator="GT",
)


def position(ebitda, inventory_change):
    return CreditPosition(
        position_id="TEST_POSITION",
        ebitda=ebitda,
        change_in_finished_goods_inventory=inventory_change,
    )


def test_r006_ratio_and_severity():
    result = EbitdaInventoryContributionRule(CONFIG).evaluate(position(1_000_000, 400_000))
    assert result.rule_id == "R006"
    assert result.value == 0.40
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r006_threshold_is_not_triggered_at_boundary():
    result = EbitdaInventoryContributionRule(CONFIG).evaluate(position(1_000_000, 300_000))
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r006_is_not_evaluable_for_missing_or_invalid_data():
    rule = EbitdaInventoryContributionRule(CONFIG)
    for ebitda, inventory_change in (
        (None, 300_000),
        (1_000_000, None),
        (0, 50_000),
        (-100_000, 50_000),
    ):
        result = rule.evaluate(position(ebitda, inventory_change))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
