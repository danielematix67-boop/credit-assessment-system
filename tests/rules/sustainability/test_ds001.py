from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.sustainability.ds001 import DebtServiceCoverageRatioRule


def make_rule() -> DebtServiceCoverageRatioRule:
    return DebtServiceCoverageRatioRule(
        RuleConfig(
            rule_id="DS001",
            rule_name="Debt Service Coverage Ratio",
            category="Debt Sustainability",
            threshold=1.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction="LOWER_IS_WORSE",
            input_fields=("cash_flow_available_for_debt_service", "debt_service"),
            calculation="ratio",
            trigger_operator="LT",
        )
    )


def test_dscr_below_threshold_triggers() -> None:
    result = make_rule().evaluate(
        SimpleNamespace(cash_flow_available_for_debt_service=80.0, debt_service=100.0)
    )
    assert result.status.value == "TRIGGERED"
    assert result.value == 0.8


def test_dscr_at_threshold_does_not_trigger() -> None:
    result = make_rule().evaluate(
        SimpleNamespace(cash_flow_available_for_debt_service=100.0, debt_service=100.0)
    )
    assert result.status.value == "NOT_TRIGGERED"


def test_dscr_missing_input_is_not_evaluable() -> None:
    result = make_rule().evaluate(
        SimpleNamespace(cash_flow_available_for_debt_service=None, debt_service=100.0)
    )
    assert result.status.value == "NOT_EVALUABLE"
