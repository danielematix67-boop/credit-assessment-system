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

    The rule itself does not implement business logic.
    Tests focus on the generic severity-resolution mechanism
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
def higher_is_worse_config() -> RuleConfig:
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


def test_rule_uses_default_severity_without_thresholds(
    base_config,
):
    rule = DummyRule(base_config)

    result = rule._result(
        value=10.0,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == base_config.severity


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
def test_rule_resolves_severity_for_higher_is_worse_direction(
    higher_is_worse_config,
    value,
    expected_severity,
):
    rule = DummyRule(higher_is_worse_config)

    result = rule._result(
        value=value,
        status=RuleStatus.TRIGGERED,
    )

    assert result.severity == expected_severity


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
def test_rule_resolves_severity_for_lower_is_worse_direction(
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


@pytest.mark.parametrize(
    "config_fixture",
    [
        "higher_is_worse_config",
        "lower_is_worse_config",
    ],
)
def test_rule_uses_default_severity_when_value_is_none(
    request,
    config_fixture,
):
    config = request.getfixturevalue(config_fixture)

    rule = DummyRule(config)

    result = rule._result(
        value=None,
        status=RuleStatus.NOT_EVALUABLE,
    )

    assert result.severity == config.severity


def test_rule_explicit_severity_overrides_threshold_resolution(
    higher_is_worse_config,
):
    rule = DummyRule(higher_is_worse_config)

    explicit_severity = RuleSeverity.LOW

    result = rule._result(
        value=5.5,
        status=RuleStatus.TRIGGERED,
        severity=explicit_severity,
    )

    assert result.severity == explicit_severity