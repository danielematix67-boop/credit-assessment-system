import pytest

from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_policy import SeverityPolicy
from src.rules.base.severity_threshold import SeverityThreshold


@pytest.fixture
def lower_is_worse_policy():
    return SeverityPolicy(
        direction=SeverityDirection.LOWER_IS_WORSE,
        thresholds=(
            SeverityThreshold(
                threshold=0.10,
                severity=RuleSeverity.LOW,
            ),
            SeverityThreshold(
                threshold=0.05,
                severity=RuleSeverity.MEDIUM,
            ),
            SeverityThreshold(
                threshold=0.00,
                severity=RuleSeverity.HIGH,
            ),
        ),
    )


@pytest.fixture
def higher_is_worse_policy():
    return SeverityPolicy(
        direction=SeverityDirection.HIGHER_IS_WORSE,
        thresholds=(
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


def test_lower_is_worse_returns_none_before_first_threshold(
    lower_is_worse_policy,
):
    first_threshold = lower_is_worse_policy.thresholds[0].threshold

    assert lower_is_worse_policy.evaluate(first_threshold + 1) is None


def test_higher_is_worse_returns_none_before_first_threshold(
    higher_is_worse_policy,
):
    first_threshold = higher_is_worse_policy.thresholds[0].threshold

    assert higher_is_worse_policy.evaluate(first_threshold - 1) is None


@pytest.mark.parametrize(
    "policy_fixture",
    [
        "lower_is_worse_policy",
        "higher_is_worse_policy",
    ],
)
def test_threshold_boundaries_are_inclusive(
    request,
    policy_fixture,
):
    policy = request.getfixturevalue(policy_fixture)

    for threshold in policy.thresholds:
        assert policy.evaluate(threshold.threshold) == threshold.severity


@pytest.mark.parametrize(
    "policy_fixture",
    [
        "lower_is_worse_policy",
        "higher_is_worse_policy",
    ],
)
def test_policy_assigns_configured_severity_at_each_threshold(
    request,
    policy_fixture,
):
    policy = request.getfixturevalue(policy_fixture)

    for threshold in policy.thresholds:
        assert policy.evaluate(threshold.threshold) == threshold.severity


def test_lower_is_worse_selects_worst_reached_severity(
    lower_is_worse_policy,
):
    worst_threshold = lower_is_worse_policy.thresholds[-1]

    assert (
        lower_is_worse_policy.evaluate(worst_threshold.threshold - 1)
        == worst_threshold.severity
    )


def test_higher_is_worse_selects_worst_reached_severity(
    higher_is_worse_policy,
):
    worst_threshold = higher_is_worse_policy.thresholds[-1]

    assert (
        higher_is_worse_policy.evaluate(worst_threshold.threshold + 1)
        == worst_threshold.severity
    )


def test_unsupported_direction_raises_value_error():
    policy = SeverityPolicy(
        direction="INVALID",
        thresholds=(),
    )

    with pytest.raises(ValueError):
        policy.evaluate(1.0)
