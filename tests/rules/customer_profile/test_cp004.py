from types import SimpleNamespace

import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.customer_profile.cp004 import ForborneExposureRule


def make_rule() -> ForborneExposureRule:
    return ForborneExposureRule(
        RuleConfig(
            rule_id="CP004",
            rule_name="Forborne Exposure",
            category="customer_profile",
            threshold=1.0,
            severity=RuleSeverity.MEDIUM,
            severity_direction="HIGHER_IS_WORSE",
            input_field="forborne",
            trigger_operator="GTE",
            comment_template=(
                "A forborne exposure is present in the customer profile and "
                "indicates an elevated credit-risk condition."
            ),
        )
    )


def test_forborne_exposure_triggers_medium_risk() -> None:
    result = make_rule().evaluate(SimpleNamespace(forborne=True))

    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert result.value is True
    assert "forborne exposure" in (result.reason or "")


def test_non_forborne_exposure_does_not_trigger() -> None:
    result = make_rule().evaluate(SimpleNamespace(forborne=False))

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW
    assert result.value is False


def test_missing_forborne_flag_is_not_evaluable() -> None:
    result = make_rule().evaluate(SimpleNamespace(forborne=None))

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


@pytest.mark.parametrize("invalid_value", [0, 1, "TRUE", "FALSE"])
def test_invalid_forborne_flag_is_not_evaluable(invalid_value: object) -> None:
    result = make_rule().evaluate(SimpleNamespace(forborne=invalid_value))

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
