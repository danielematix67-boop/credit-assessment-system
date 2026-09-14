from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.behavioural.b002 import ProlongedOverdraftRule


def make_rule() -> ProlongedOverdraftRule:
    return ProlongedOverdraftRule(
        RuleConfig(
            rule_id="B002",
            rule_name="Prolonged Overdraft",
            category="overdraft",
            threshold=10.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction="HIGHER_IS_WORSE",
            input_field="overdraft_days",
            trigger_operator="GT",
        )
    )


def test_overdraft_above_threshold_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(overdraft_days=11)).status.value == "TRIGGERED"


def test_overdraft_at_threshold_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(overdraft_days=10)).status.value == "NOT_TRIGGERED"


def test_missing_overdraft_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(overdraft_days=None)).status.value == "NOT_EVALUABLE"
