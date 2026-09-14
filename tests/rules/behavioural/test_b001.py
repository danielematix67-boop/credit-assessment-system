from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.behavioural.b001 import HighCreditUtilizationRule


def make_rule() -> HighCreditUtilizationRule:
    return HighCreditUtilizationRule(
        RuleConfig(
            rule_id="B001",
            rule_name="High Credit Utilization",
            category="utilization",
            threshold=0.90,
            severity=RuleSeverity.MEDIUM,
            severity_direction="HIGHER_IS_WORSE",
            input_field="average_utilization",
            trigger_operator="GT",
        )
    )


def test_high_utilization_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(average_utilization=0.95)).status.value == "TRIGGERED"


def test_threshold_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(average_utilization=0.90)).status.value == "NOT_TRIGGERED"


def test_missing_utilization_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(average_utilization=None)).status.value == "NOT_EVALUABLE"
