from dataclasses import dataclass

import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@dataclass
class DummyPosition:
    value: float | None = None


class DummyRule(Rule):
    """
    Minimal rule implementation used to test the Rule base class.

    The rule itself does not implement any business logic.
    The tests focus on the generic severity-resolution mechanism
    provided by the Rule base class.
    """

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:

        return self._result(
            value=position.revenue_growth,
            status=RuleStatus.TRIGGERED,
        )


@pytest.fixture
def base_config() -> RuleConfig:
    return RuleConfig(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        threshold=0.0,
        severity=RuleSeverity.LOW,
    )


@pytest.fixture
def multi_severity_config() -> RuleConfig:
    return RuleConfig(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        threshold=3.0,
        severity=RuleSeverity.LOW,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        severity_thresholds=(
            SeverityThreshold(
                threshold=3.0,
                severity=RuleSeverity.LOW,
            ),
            SeverityThreshold(
                threshold=4.0,
                severity=RuleSeverity.MEDIUM,
            ),
            SeverityThreshold(
                threshold=5.0,
                severity=RuleSeverity.HIGH,
            ),
        ),
    )


@pytest.fixture
def lower_is_worse_config() -> RuleConfig:
    return RuleConfig(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        threshold=-10.0,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.LOWER_IS_WORSE,
        severity_thresholds=(
            SeverityThreshold(
                threshold=-10.0,
                severity=RuleSeverity.MEDIUM,
            ),
            SeverityThreshold(
                threshold=-20.0,
                severity=RuleSeverity.HIGH,
            ),
        ),
    )


def test_rule_uses_default_severity_when_no_thresholds_are_configured(
    base_config,
):
    rule = DummyRule(base_config)

    result = rule._result(
        value=10.0,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == RuleSeverity.LOW


@pytest.mark.parametrize(
    "value, expected_severity",
    [
        (2.0, RuleSeverity.LOW),
        (3.0, RuleSeverity.LOW),
        (3.5, RuleSeverity.LOW),
        (4.0, RuleSeverity.MEDIUM),
        (4.5, RuleSeverity.MEDIUM),
        (5.0, RuleSeverity.HIGH),
        (5.5, RuleSeverity.HIGH),
    ],
)
def test_rule_resolves_severity_from_thresholds(
    multi_severity_config,
    value,
    expected_severity,
):
    rule = DummyRule(multi_severity_config)

    result = rule._result(
        value=value,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == expected_severity


def test_rule_uses_highest_reached_threshold(
    multi_severity_config,
):
    rule = DummyRule(multi_severity_config)

    result = rule._result(
        value=5.5,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == RuleSeverity.HIGH


@pytest.mark.parametrize(
    "value, expected_severity",
    [
        (-5.0, RuleSeverity.MEDIUM),
        (-10.0, RuleSeverity.MEDIUM),
        (-15.0, RuleSeverity.MEDIUM),
        (-20.0, RuleSeverity.HIGH),
        (-25.0, RuleSeverity.HIGH),
    ],
)
def test_rule_resolves_severity_when_lower_values_are_worse(
    lower_is_worse_config,
    value,
    expected_severity,
):
    rule = DummyRule(lower_is_worse_config)

    result = rule._result(
        value=value,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == expected_severity


def test_rule_uses_lowest_reached_threshold_when_lower_values_are_worse(
    lower_is_worse_config,
):
    rule = DummyRule(lower_is_worse_config)

    result = rule._result(
        value=-25.0,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == RuleSeverity.HIGH


def test_rule_returns_default_severity_when_value_is_none(
    multi_severity_config,
):
    rule = DummyRule(multi_severity_config)

    result = rule._result(
        value=None,
        status=RuleStatus.NOT_EVALUABLE,
    )

    assert result.severity == RuleSeverity.LOW


def test_rule_explicit_severity_overrides_threshold_resolution(
    multi_severity_config,
):
    rule = DummyRule(multi_severity_config)

    result = rule._result(
        value=5.5,
        status=RuleStatus.TRIGGERED,
        severity=RuleSeverity.LOW,
    )

    assert result.severity == RuleSeverity.LOW

def test_lower_is_worse_debug(
    lower_is_worse_config,
):
    rule = DummyRule(lower_is_worse_config)

    print(
        "\nDIRECTION:",
        rule.config.severity_direction,
    )

    print(
        "THRESHOLDS:",
        rule.config.severity_thresholds,
    )

    print(
        "SEVERITY -20:",
        rule._severity(-20.0),
    )

    print(
        "SEVERITY -25:",
        rule._severity(-25.0),
    )

    assert True