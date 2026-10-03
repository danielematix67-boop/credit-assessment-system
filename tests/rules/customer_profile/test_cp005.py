from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.customer_profile.cp005 import ShortBankingRelationshipRule


def make_rule() -> ShortBankingRelationshipRule:
    return ShortBankingRelationshipRule(
        RuleConfig(
            rule_id="CP005",
            rule_name="Short Banking Relationship",
            category="customer_profile",
            threshold=2.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction="LOWER_IS_WORSE",
            input_field="relationship_years",
            trigger_operator="LTE",
            comment_template=(
                "The banking relationship has lasted {value:.0f} years, "
                "indicating a limited observable relationship history with the customer."
            ),
        )
    )


def test_short_banking_relationship_triggers_at_threshold() -> None:
    result = make_rule().evaluate(SimpleNamespace(relationship_years=2))

    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert result.value == 2.0
    assert result.threshold == 2.0


def test_longer_banking_relationship_does_not_trigger() -> None:
    result = make_rule().evaluate(SimpleNamespace(relationship_years=3))

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert result.value == 3.0


def test_missing_banking_relationship_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(relationship_years=None))

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == RuleSeverity.MEDIUM


def test_invalid_banking_relationship_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(relationship_years="2"))

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_banking_relationship_uses_configured_comment() -> None:
    result = make_rule().evaluate(SimpleNamespace(relationship_years=1))

    assert result.reason == (
        "The banking relationship has lasted 1 years, indicating a limited "
        "observable relationship history with the customer."
    )
