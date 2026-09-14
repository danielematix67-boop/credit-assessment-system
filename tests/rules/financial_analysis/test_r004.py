from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r004 import NfpToEbitdaRule


def make_rule(**kwargs) -> NfpToEbitdaRule:
    return NfpToEbitdaRule(
        RuleConfig(
            rule_id="R004",
            name="NFP / EBITDA leverage",
            description="Tests leverage deterioration.",
            threshold=5.0,
            high_threshold=7.0,
            severity_direction="higher_is_worse",
            trigger_operator="gt",
            comment_template="NFP to EBITDA threshold triggered.",
            **kwargs,
        )
    )


def test_high_leverage_triggers_high_severity() -> None:
    result = make_rule().evaluate(CreditPosition(position_id="TEST", nfp_to_ebitda=8.0))
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity.value == "HIGH"


def test_leverage_at_threshold_does_not_trigger() -> None:
    result = make_rule().evaluate(CreditPosition(position_id="TEST", nfp_to_ebitda=5.0))
    assert result.status == RuleStatus.NOT_TRIGGERED


def test_missing_leverage_is_not_evaluable() -> None:
    result = make_rule().evaluate(CreditPosition(position_id="TEST", nfp_to_ebitda=None))
    assert result.status == RuleStatus.NOT_EVALUABLE
