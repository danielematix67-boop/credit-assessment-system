from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r003 import EbitdaMarginRule


def make_rule(**kwargs) -> EbitdaMarginRule:
    return EbitdaMarginRule(
        RuleConfig(
            rule_id="R003",
            rule_name="EBITDA margin deterioration",
            category="profitability",
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction=SeverityDirection.LOWER_IS_WORSE,
            severity_thresholds=(),
            input_field="ebitda_margin",
            comment_template="EBITDA margin threshold triggered.",
            trigger_operator="LT",
            **kwargs,
        )
    )


def test_negative_margin_triggers_medium_severity() -> None:
    result = make_rule().evaluate(
        CreditPosition(position_id="TEST", ebitda_margin=-0.05)
    )
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_positive_margin_does_not_trigger() -> None:
    result = make_rule().evaluate(
        CreditPosition(position_id="TEST", ebitda_margin=0.05)
    )
    assert result.status == RuleStatus.NOT_TRIGGERED


def test_missing_margin_is_not_evaluable() -> None:
    result = make_rule().evaluate(
        CreditPosition(position_id="TEST", ebitda_margin=None)
    )
    assert result.status == RuleStatus.NOT_EVALUABLE
