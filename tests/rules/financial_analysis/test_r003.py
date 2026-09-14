from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r003 import EbitdaMarginRule


def make_rule(**kwargs) -> EbitdaMarginRule:
    return EbitdaMarginRule(
        RuleConfig(
            rule_id="R003",
            name="EBITDA margin",
            description="Tests EBITDA margin deterioration.",
            threshold=0.0,
            high_threshold=-0.10,
            severity_direction="lower_is_worse",
            trigger_operator="lt",
            comment_template="EBITDA margin threshold triggered.",
            **kwargs,
        )
    )


def test_negative_margin_triggers_high_severity() -> None:
    result = make_rule().evaluate(CreditPosition(position_id="TEST", ebitda_margin=-0.15))
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity.value == "HIGH"


def test_positive_margin_does_not_trigger() -> None:
    result = make_rule().evaluate(CreditPosition(position_id="TEST", ebitda_margin=0.05))
    assert result.status == RuleStatus.NOT_TRIGGERED


def test_missing_margin_is_not_evaluable() -> None:
    result = make_rule().evaluate(CreditPosition(position_id="TEST", ebitda_margin=None))
    assert result.status == RuleStatus.NOT_EVALUABLE
