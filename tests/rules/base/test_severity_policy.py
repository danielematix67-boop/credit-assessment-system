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


def test_lower_is_worse_returns_none_when_no_threshold_is_reached(
    lower_is_worse_policy,
):
    assert (
        lower_is_worse_policy.evaluate(0.11)
        is None
    )


@pytest.mark.parametrize(
    "value, expected_severity",
    [
        (0.10, RuleSeverity.LOW),
        (0.09, RuleSeverity.LOW),
        (0.05, RuleSeverity.MEDIUM),
        (0.049, RuleSeverity.MEDIUM),
        (0.00, RuleSeverity.HIGH),
        (-0.01, RuleSeverity.HIGH),
    ],
)
def test_lower_is_worse_assigns_expected_severity(
    lower_is_worse_policy,
    value,
    expected_severity,
):
    assert (
        lower_is_worse_policy.evaluate(value)
        == expected_severity
    )


@pytest.mark.parametrize(
    "value, expected_severity",
    [
        (2.9, None),
        (3.0, RuleSeverity.LOW),
        (3.1, RuleSeverity.LOW),
        (4.0, RuleSeverity.MEDIUM),
        (4.1, RuleSeverity.MEDIUM),
        (5.0, RuleSeverity.HIGH),
        (5.1, RuleSeverity.HIGH),
    ],
)
def test_higher_is_worse_assigns_expected_severity(
    higher_is_worse_policy,
    value,
    expected_severity,
):
    assert (
        higher_is_worse_policy.evaluate(value)
        == expected_severity
    )


def test_lower_is_worse_boundary_is_inclusive(
    lower_is_worse_policy,
):
    assert (
        lower_is_worse_policy.evaluate(0.10)
        == RuleSeverity.LOW
    )

    assert (
        lower_is_worse_policy.evaluate(0.05)
        == RuleSeverity.MEDIUM
    )

    assert (
        lower_is_worse_policy.evaluate(0.00)
        == RuleSeverity.HIGH
    )


def test_higher_is_worse_boundary_is_inclusive(
    higher_is_worse_policy,
):
    assert (
        higher_is_worse_policy.evaluate(3.0)
        == RuleSeverity.LOW
    )

    assert (
        higher_is_worse_policy.evaluate(4.0)
        == RuleSeverity.MEDIUM
    )

    assert (
        higher_is_worse_policy.evaluate(5.0)
        == RuleSeverity.HIGH
    )


def test_unsupported_direction_raises_value_error():
    policy = SeverityPolicy(
        direction="INVALID",
        thresholds=(),
    )

    with pytest.raises(ValueError):
        policy.evaluate(1.0)