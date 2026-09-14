from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r003 import EbitdaMarginRule

CONFIG = RuleConfig(
    rule_id="R003",
    rule_name="EBITDA margin deterioration",
    category="profitability",
    threshold=0.0,
    severity=RuleSeverity.MEDIUM,
    severity_direction=SeverityDirection.LOWER_IS_WORSE,
    input_field="ebitda_margin",
    trigger_operator="LT",
)


def test_ebitda_margin_rule_triggered():
    result = EbitdaMarginRule(CONFIG).evaluate(
        CreditPosition(position_id="POS001", ebitda_margin=-0.05)
    )
    assert result.rule_id == CONFIG.rule_id
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == -0.05


def test_ebitda_margin_rule_not_triggered():
    result = EbitdaMarginRule(CONFIG).evaluate(
        CreditPosition(position_id="POS002", ebitda_margin=0.12)
    )
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.12


def test_ebitda_margin_rule_not_evaluable_when_none():
    result = EbitdaMarginRule(CONFIG).evaluate(
        CreditPosition(position_id="POS003", ebitda_margin=None)
    )
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
