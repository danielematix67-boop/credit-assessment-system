from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r001 import RevenueGrowthRule

CONFIG = RuleConfig(
    rule_id="R001", rule_name="Revenue deterioration", category="revenue",
    threshold=-0.10, severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.LOWER_IS_WORSE,
    severity_thresholds=(SeverityThreshold(threshold=-0.10, severity=RuleSeverity.MEDIUM), SeverityThreshold(threshold=-0.20, severity=RuleSeverity.HIGH)),
    input_field="revenue_growth", trigger_operator="LT",
)


def test_r001_dynamic_severity_and_trigger():
    rule = RevenueGrowthRule(CONFIG)
    for value, status, severity in (
        (0.05, RuleStatus.NOT_TRIGGERED, RuleSeverity.LOW),
        (-0.10, RuleStatus.NOT_TRIGGERED, RuleSeverity.MEDIUM),
        (-0.15, RuleStatus.TRIGGERED, RuleSeverity.MEDIUM),
        (-0.20, RuleStatus.TRIGGERED, RuleSeverity.HIGH),
    ):
        result = rule.evaluate(CreditPosition(position_id="P", revenue_growth=value))
        assert result.status == status
        assert result.severity == severity


def test_r001_none_is_not_evaluable():
    result = RevenueGrowthRule(CONFIG).evaluate(CreditPosition(position_id="P", revenue_growth=None))
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_r001_uses_configured_operator():
    config = RuleConfig(rule_id="R001_CUSTOM", rule_name="Custom", category="revenue", threshold=0.10, severity=RuleSeverity.MEDIUM, severity_direction=SeverityDirection.LOWER_IS_WORSE, input_field="revenue_growth", trigger_operator="GTE")
    result = RevenueGrowthRule(config).evaluate(CreditPosition(position_id="P", revenue_growth=0.10))
    assert result.status == RuleStatus.TRIGGERED
