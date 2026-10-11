from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r009 import OperatingGrantsIncidenceRule

CONFIG = RuleConfig(
    rule_id="R009",
    rule_name="Operating grants incidence on production value",
    category="profitability_quality",
    threshold=0.10,
    severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=0.10, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=0.20, severity=RuleSeverity.HIGH),
    ),
    input_fields=("operating_grants", "production_value"),
    calculation="ratio",
    trigger_operator="GT",
)


def position(grants, production_value):
    return CreditPosition(
        position_id="TEST_POSITION",
        operating_grants=grants,
        production_value=production_value,
    )


def test_r009_not_triggered_below_threshold():
    result = OperatingGrantsIncidenceRule(CONFIG).evaluate(position(50, 1000))
    assert result.value == 0.05
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_r009_medium_severity_above_ten_percent():
    result = OperatingGrantsIncidenceRule(CONFIG).evaluate(position(150, 1000))
    assert result.value == 0.15
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r009_high_severity_above_twenty_percent():
    result = OperatingGrantsIncidenceRule(CONFIG).evaluate(position(250, 1000))
    assert result.value == 0.25
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_r009_ten_percent_boundary_is_exclusive():
    result = OperatingGrantsIncidenceRule(CONFIG).evaluate(position(100, 1000))
    assert result.value == 0.10
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_r009_not_evaluable_for_missing_or_invalid_inputs():
    rule = OperatingGrantsIncidenceRule(CONFIG)
    for grants, production_value in (
        (None, 1000),
        (100, None),
        (100, 0),
        (100, -1),
        (-10, 1000),
    ):
        result = rule.evaluate(position(grants, production_value))
        assert result.status == RuleStatus.NOT_EVALUABLE
        assert result.value is None
