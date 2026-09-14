from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.customer_profile.cp003 import BusinessHistoryRule


def make_rule() -> BusinessHistoryRule:
    return BusinessHistoryRule(RuleConfig(rule_id="CP003", rule_name="Business history", category="customer_profile", threshold=5.0, severity=RuleSeverity.MEDIUM, severity_direction="LOWER_IS_WORSE", input_field="business_history_years", trigger_operator="LTE"))


def test_short_business_history_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(business_history_years=3)).status.value == "TRIGGERED"


def test_long_business_history_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(business_history_years=10)).status.value == "NOT_TRIGGERED"


def test_missing_business_history_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(business_history_years=None)).status.value == "NOT_EVALUABLE"
