from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.sustainability.ds003 import CashFlowDebtServiceBufferRule


def make_rule() -> CashFlowDebtServiceBufferRule:
    return CashFlowDebtServiceBufferRule(RuleConfig(rule_id="DS003", rule_name="Cash Flow Debt-Service Buffer", category="Debt Sustainability", threshold=0.0, severity=RuleSeverity.MEDIUM, severity_direction="LOWER_IS_WORSE", input_fields=("cash_flow_available_for_debt_service", "debt_service"), calculation="difference", trigger_operator="LT"))


def test_negative_buffer_triggers() -> None:
    result = make_rule().evaluate(SimpleNamespace(cash_flow_available_for_debt_service=80.0, debt_service=100.0))
    assert result.status.value == "TRIGGERED"
    assert result.value == -20.0


def test_zero_buffer_does_not_trigger() -> None:
    result = make_rule().evaluate(SimpleNamespace(cash_flow_available_for_debt_service=100.0, debt_service=100.0))
    assert result.status.value == "NOT_TRIGGERED"


def test_missing_input_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(cash_flow_available_for_debt_service=None, debt_service=100.0))
    assert result.status.value == "NOT_EVALUABLE"
