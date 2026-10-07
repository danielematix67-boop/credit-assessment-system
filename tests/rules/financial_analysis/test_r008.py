from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r008 import OperatingLeverageRule

CONFIG = RuleConfig(
    rule_id="R008",
    rule_name="Operating leverage",
    category="operating_leverage",
    threshold=3.00,
    severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=3.00, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=5.00, severity=RuleSeverity.HIGH),
    ),
    input_fields=("contribution_margin", "net_operating_margin"),
    calculation="ratio",
    trigger_operator="GT",
)


def position(contribution_margin, ebit):
    return CreditPosition(
        position_id="TEST_POSITION",
        contribution_margin=contribution_margin,
        net_operating_margin=ebit,
    )


def test_r008_ratio_and_medium_severity():
    result = OperatingLeverageRule(CONFIG).evaluate(position(400_000, 100_000))
    assert result.rule_id == "R008"
    assert result.value == 4.00
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r008_high_severity():
    result = OperatingLeverageRule(CONFIG).evaluate(position(600_000, 100_000))
    assert result.value == 6.00
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_r008_threshold_is_exclusive():
    result = OperatingLeverageRule(CONFIG).evaluate(position(300_000, 100_000))
    assert result.value == 3.00
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r008_is_not_evaluable_for_missing_or_non_positive_ebit():
    rule = OperatingLeverageRule(CONFIG)
    for contribution_margin, ebit in (
        (None, 100_000),
        (400_000, None),
        (400_000, 0),
        (400_000, -100_000),
    ):
        result = rule.evaluate(position(contribution_margin, ebit))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
