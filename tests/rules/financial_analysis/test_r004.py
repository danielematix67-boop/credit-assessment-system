from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r004 import NfpToEbitdaRule


def make_rule(**kwargs) -> NfpToEbitdaRule:
    return NfpToEbitdaRule(
        RuleConfig(
            rule_id="R004",
            rule_name="nfp / EBITDA leverage",
            category="leverage",
            threshold=5.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction=SeverityDirection.HIGHER_IS_WORSE,
            severity_thresholds=(
                SeverityThreshold(5.0, RuleSeverity.MEDIUM),
                SeverityThreshold(7.0, RuleSeverity.HIGH),
            ),
            input_field="nfp_to_ebitda",
            comment_template="NFP to EBITDA threshold triggered.",
            trigger_operator="GT",
            **kwargs,
        )
    )


def test_high_leverage_triggers_high_severity() -> None:
    result = make_rule().evaluate(
        CreditPosition(position_id="TEST", nfp_to_ebitda=8.0)
    )
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_leverage_at_threshold_does_not_trigger() -> None:
    result = make_rule().evaluate(
        CreditPosition(position_id="TEST", nfp_to_ebitda=5.0)
    )
    assert result.status == RuleStatus.NOT_TRIGGERED


def test_missing_leverage_is_not_evaluable() -> None:
    result = make_rule().evaluate(
        CreditPosition(position_id="TEST", nfp_to_ebitda=None)
    )
    assert result.status == RuleStatus.NOT_EVALUABLE
