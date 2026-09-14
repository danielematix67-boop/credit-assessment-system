from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.behavioural.b003 import PaymentDelayRule


def make_rule() -> PaymentDelayRule:
    return PaymentDelayRule(RuleConfig(rule_id="B003", rule_name="Payment Delay", category="payment_behaviour", threshold=30.0, severity=RuleSeverity.MEDIUM, severity_direction="HIGHER_IS_WORSE", input_field="payment_delay_days", trigger_operator="GT"))


def test_payment_delay_above_threshold_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(payment_delay_days=31)).status.value == "TRIGGERED"


def test_payment_delay_at_threshold_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(payment_delay_days=30)).status.value == "NOT_TRIGGERED"


def test_missing_payment_delay_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(payment_delay_days=None)).status.value == "NOT_EVALUABLE"
