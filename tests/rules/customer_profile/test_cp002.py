from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.customer_profile.cp002 import PreviousRestructuringRule


def make_rule() -> PreviousRestructuringRule:
    return PreviousRestructuringRule(
        RuleConfig(
            rule_id="CP002",
            rule_name="Previous Restructuring",
            category="customer_profile",
            threshold=1.0,
            severity=RuleSeverity.HIGH,
            severity_direction="HIGHER_IS_WORSE",
            input_field="previous_restructuring",
            trigger_operator="GTE",
        )
    )


def test_previous_restructuring_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(previous_restructuring=1)).status.value == "TRIGGERED"


def test_no_previous_restructuring_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(previous_restructuring=0)).status.value == "NOT_TRIGGERED"


def test_missing_restructuring_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(previous_restructuring=None)).status.value == "NOT_EVALUABLE"
