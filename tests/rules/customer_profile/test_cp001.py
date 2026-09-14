from types import SimpleNamespace

import pytest

from src.models.ews_score import EwsScoreClass
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.customer_profile.cp001 import EwsScoreClassRule


def make_rule() -> EwsScoreClassRule:
    return EwsScoreClassRule(
        RuleConfig(
            rule_id="CP001",
            rule_name="EWS Score Class",
            category="customer_profile",
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction="HIGHER_IS_WORSE",
            input_field="ews_score_class",
            trigger_operator="GTE",
        )
    )


@pytest.mark.parametrize(
    ("score_class", "expected_severity"),
    [
        (EwsScoreClass.YELLOW, RuleSeverity.MEDIUM),
        (EwsScoreClass.ORANGE, RuleSeverity.MEDIUM),
        (EwsScoreClass.LIGHT_RED, RuleSeverity.HIGH),
    ],
)
def test_risk_ews_classes_trigger_with_expected_severity(
    score_class: EwsScoreClass,
    expected_severity: RuleSeverity,
) -> None:
    result = make_rule().evaluate(SimpleNamespace(ews_score_class=score_class))

    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == expected_severity
    assert score_class.value in (result.reason or "")


def test_green_ews_class_does_not_trigger() -> None:
    result = make_rule().evaluate(
        SimpleNamespace(ews_score_class=EwsScoreClass.GREEN)
    )

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW
    assert "GREEN" in (result.reason or "")


def test_string_ews_class_is_supported() -> None:
    result = make_rule().evaluate(SimpleNamespace(ews_score_class="ORANGE"))

    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_missing_ews_score_class_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(ews_score_class=None))

    assert result.status == RuleStatus.NOT_EVALUABLE


def test_invalid_ews_score_class_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(ews_score_class="PURPLE"))

    assert result.status == RuleStatus.NOT_EVALUABLE
