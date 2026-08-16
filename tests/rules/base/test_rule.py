import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class DummyRule(Rule):
    """
    Minimal rule implementation used to test the Rule base class.

    The rule itself does not implement business logic.
    Tests focus on the generic mechanisms provided by the
    Rule base class, including severity resolution and
    rule-reference generation.
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


def test_rule_result_contains_rule_reference(
    base_config,
):
    rule = DummyRule(base_config)

    result = rule._result(
        value=10.0,
        status=RuleStatus.TRIGGERED,
        reason="Value exceeded the configured threshold.",
    )

    assert result.rule_id == base_config.rule_id
    assert result.rule_name == base_config.rule_name
    assert result.reason == (
        "[TEST_RULE - Test rule] "
        "Value exceeded the configured threshold."
    )


def test_rule_result_generates_default_reason_without_reason_input(
    base_config,
):
    rule = DummyRule(base_config)

    result = rule._result(
        value=10.0,
        status=RuleStatus.TRIGGERED,
    )

    assert result.reason == (
        "[TEST_RULE - Test rule] "
        "Rule evaluation completed."
    )


def test_not_evaluable_result_contains_rule_reference(
    base_config,
):
    rule = DummyRule(base_config)

    result = rule._not_evaluable(
        reason="Required input is not available.",
    )

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.reason == (
        "[TEST_RULE - Test rule] "
        "Required input is not available."
    )
