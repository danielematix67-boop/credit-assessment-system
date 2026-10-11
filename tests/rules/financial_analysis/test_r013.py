from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r013 import TaxDebtConcentrationRule

CONFIG = RuleConfig(
    rule_id="R013",
    rule_name="Tax debt concentration in total liabilities",
    category="leverage",
    threshold=0.15,
    severity=RuleSeverity.MEDIUM,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=0.15, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=0.25, severity=RuleSeverity.HIGH),
    ),
    input_fields=("tax_debt", "total_liabilities"),
    calculation="ratio",
    trigger_operator="GT",
)


def position(tax_debt, total_liabilities):
    return CreditPosition(
        position_id="TEST_POSITION",
        tax_debt=tax_debt,
        total_liabilities=total_liabilities,
    )


def test_r013_does_not_trigger_below_threshold():
    result = TaxDebtConcentrationRule(CONFIG).evaluate(position(100, 1000))
    assert result.value == 0.10
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r013_triggers_medium_above_fifteen_percent():
    result = TaxDebtConcentrationRule(CONFIG).evaluate(position(200, 1000))
    assert result.value == 0.20
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r013_triggers_high_above_twenty_five_percent():
    result = TaxDebtConcentrationRule(CONFIG).evaluate(position(300, 1000))
    assert result.value == 0.30
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_r013_fifteen_percent_boundary_is_exclusive():
    result = TaxDebtConcentrationRule(CONFIG).evaluate(position(150, 1000))
    assert result.value == 0.15
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r013_is_not_evaluable_for_missing_or_invalid_inputs():
    rule = TaxDebtConcentrationRule(CONFIG)
    for tax_debt, total_liabilities in (
        (None, 1000),
        (100, None),
        (-1, 1000),
        (100, 0),
        (100, -1),
        (float("nan"), 1000),
        (100, float("inf")),
        (True, 1000),
    ):
        result = rule.evaluate(position(tax_debt, total_liabilities))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
