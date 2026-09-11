import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial.profitability.interest_coverage_ratio import (
    InterestCoverageRatioRule,
)

RULE_ID = "R007"
RULE_NAME = "Interest coverage ratio"
CATEGORY = "profitability"
THRESHOLD = 2.00
DEFAULT_SEVERITY = RuleSeverity.LOW


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id=RULE_ID,
        rule_name=RULE_NAME,
        category=CATEGORY,
        threshold=THRESHOLD,
        severity=DEFAULT_SEVERITY,
        severity_direction=SeverityDirection.LOWER_IS_WORSE,
        severity_thresholds=(
            SeverityThreshold(threshold=2.00, severity=RuleSeverity.MEDIUM),
            SeverityThreshold(threshold=1.00, severity=RuleSeverity.HIGH),
        ),
        input_fields=("ebitda", "interest_expense"),
        calculation="ratio",
        trigger_operator="LT",
    )


@pytest.fixture
def rule(rule_config):
    return InterestCoverageRatioRule(rule_config)


def make_position(
    *,
    ebitda: float | None,
    interest_expense: float | None,
) -> CreditPosition:
    return CreditPosition(
        position_id="TEST_POSITION",
        ebitda=ebitda,
        interest_expense=interest_expense,
    )


def assert_result_metadata(result, config):
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold


@pytest.mark.parametrize(
    (
        "ebitda",
        "interest_expense",
        "expected_value",
        "expected_status",
        "expected_severity",
    ),
    [
        (50_000, 50_000, 1.00, RuleStatus.TRIGGERED, RuleSeverity.HIGH),
        (75_000, 50_000, 1.50, RuleStatus.TRIGGERED, RuleSeverity.MEDIUM),
        (100_000, 50_000, 2.00, RuleStatus.NOT_TRIGGERED, RuleSeverity.MEDIUM),
        (150_000, 50_000, 3.00, RuleStatus.NOT_TRIGGERED, RuleSeverity.LOW),
    ],
)
def test_interest_coverage_ratio_rule_evaluates_configured_ratio(
    rule,
    rule_config,
    ebitda,
    interest_expense,
    expected_value,
    expected_status,
    expected_severity,
):
    position = make_position(
        ebitda=ebitda,
        interest_expense=interest_expense,
    )

    result = rule.evaluate(position)

    assert_result_metadata(result, rule_config)
    assert result.value == expected_value
    assert result.status == expected_status
    assert result.severity == expected_severity


def test_interest_coverage_ratio_threshold_is_exclusive(rule):
    position = make_position(ebitda=100_000, interest_expense=50_000)

    result = rule.evaluate(position)

    assert result.value == 2.00
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


@pytest.mark.parametrize(
    ("ebitda", "interest_expense"),
    [
        (None, 50_000),
        (100_000, None),
        (100_000, 0),
        (100_000, -10_000),
    ],
)
def test_interest_coverage_ratio_rule_is_not_evaluable(
    rule,
    rule_config,
    ebitda,
    interest_expense,
):
    position = make_position(
        ebitda=ebitda,
        interest_expense=interest_expense,
    )

    result = rule.evaluate(position)

    assert_result_metadata(result, rule_config)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == rule_config.severity


def test_interest_coverage_ratio_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="CUSTOM_RULE",
        rule_name="Custom interest coverage ratio",
        category=CATEGORY,
        threshold=1.50,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.LOWER_IS_WORSE,
        input_fields=("ebitda", "interest_expense"),
        calculation="ratio",
        trigger_operator="LT",
    )

    position = make_position(ebitda=75_000, interest_expense=50_000)

    result = InterestCoverageRatioRule(config).evaluate(position)

    assert_result_metadata(result, config)
    assert result.value == 1.50
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
