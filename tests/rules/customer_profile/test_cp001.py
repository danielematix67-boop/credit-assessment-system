from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.customer_profile.cp001 import ActiveEwsRule


def make_rule() -> ActiveEwsRule:
    return ActiveEwsRule(
        RuleConfig(
            rule_id="CP001",
            rule_name="Active EWS",
            category="customer_profile",
            threshold=1.0,
            severity=RuleSeverity.HIGH,
            severity_direction="HIGHER_IS_WORSE",
            input_field="active_ews",
            trigger_operator="GTE",
        )
    )


def test_active_ews_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(active_ews=1)).status.value == "TRIGGERED"


def test_inactive_ews_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(active_ews=0)).status.value == "NOT_TRIGGERED"


def test_missing_ews_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(active_ews=None)).status.value == "NOT_EVALUABLE"
