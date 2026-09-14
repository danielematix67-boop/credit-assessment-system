from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r002 import NegativeEbitdaRule

CONFIG = RuleConfig(rule_id="R002", rule_name="Negative EBITDA", category="profitability", threshold=0.0, severity=RuleSeverity.HIGH, severity_direction=SeverityDirection.LOWER_IS_WORSE, input_field="ebitda", trigger_operator="LT")


def test_r002_negative_ebitda_triggers():
    result = NegativeEbitdaRule(CONFIG).evaluate(CreditPosition(position_id="P", ebitda=-50_000))
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == -50_000


def test_r002_positive_ebitda_does_not_trigger():
    result = NegativeEbitdaRule(CONFIG).evaluate(CreditPosition(position_id="P", ebitda=250_000))
    assert result.status == RuleStatus.NOT_TRIGGERED


def test_r002_none_is_not_evaluable():
    result = NegativeEbitdaRule(CONFIG).evaluate(CreditPosition(position_id="P", ebitda=None))
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
