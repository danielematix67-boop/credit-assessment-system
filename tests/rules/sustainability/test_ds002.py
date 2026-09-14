from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.sustainability.ds002 import DebtServiceToEbitdaRule


def make_rule() -> DebtServiceToEbitdaRule:
    return DebtServiceToEbitdaRule(RuleConfig(rule_id="DS002", rule_name="Debt Service / EBITDA", category="Debt Sustainability", threshold=1.0, severity=RuleSeverity.MEDIUM, severity_direction="HIGHER_IS_WORSE", input_fields=("debt_service", "ebitda"), calculation="ratio", trigger_operator="GT"))


def test_above_threshold_triggers() -> None:
    result = make_rule().evaluate(SimpleNamespace(debt_service=120.0, ebitda=100.0))
    assert result.status.value == "TRIGGERED"
    assert result.value == 1.2


def test_at_threshold_does_not_trigger() -> None:
    result = make_rule().evaluate(SimpleNamespace(debt_service=100.0, ebitda=100.0))
    assert result.status.value == "NOT_TRIGGERED"


def test_missing_input_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(debt_service=100.0, ebitda=None))
    assert result.status.value == "NOT_EVALUABLE"
