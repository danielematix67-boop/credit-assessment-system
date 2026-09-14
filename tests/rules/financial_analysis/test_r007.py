from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r007 import InterestCoverageRatioRule

CONFIG = RuleConfig(
    rule_id="R007",
    rule_name="Interest coverage ratio",
    category="profitability",
    threshold=2.00,
    severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.LOWER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=2.00, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=1.00, severity=RuleSeverity.HIGH),
    ),
    input_fields=("ebitda", "interest_expense"),
    calculation="ratio",
    trigger_operator="LT",
)


def position(ebitda, interest_expense):
    return CreditPosition(
        position_id="TEST_POSITION",
        ebitda=ebitda,
        interest_expense=interest_expense,
    )


def test_r007_ratio_and_severity():
    rule = InterestCoverageRatioRule(CONFIG)
    result = rule.evaluate(position(75_000, 50_000))
    assert result.rule_id == "R007"
    assert result.value == 1.50
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r007_threshold_is_exclusive():
    result = InterestCoverageRatioRule(CONFIG).evaluate(position(100_000, 50_000))
    assert result.value == 2.00
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r007_is_not_evaluable_for_invalid_data():
    rule = InterestCoverageRatioRule(CONFIG)
    for ebitda, interest_expense in (
        (None, 50_000),
        (100_000, None),
        (100_000, 0),
        (100_000, -10_000),
    ):
        result = rule.evaluate(position(ebitda, interest_expense))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None


def test_r007_uses_configured_threshold():
    config = RuleConfig(
        rule_id="R007_CUSTOM",
        rule_name="Custom interest coverage ratio",
        category="profitability",
        threshold=1.50,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.LOWER_IS_WORSE,
        input_fields=("ebitda", "interest_expense"),
        calculation="ratio",
        trigger_operator="LT",
    )
    result = InterestCoverageRatioRule(config).evaluate(position(75_000, 50_000))
    assert result.value == 1.50
    assert result.status == RuleStatus.NOT_TRIGGERED
