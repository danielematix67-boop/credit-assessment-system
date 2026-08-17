import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.base.severity_direction import SeverityDirection
from src.rules.financial.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


RULE_ID = "TEST_RULE"
RULE_NAME = "Test interest expense to EBITDA"
CATEGORY = "test"
THRESHOLD = 0.60
DEFAULT_SEVERITY = RuleSeverity.LOW


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id=RULE_ID,
        rule_name=RULE_NAME,
        category=CATEGORY,
        threshold=THRESHOLD,
        severity=DEFAULT_SEVERITY,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        severity_thresholds=(
            SeverityThreshold(
                threshold=0.40,
                severity=RuleSeverity.MEDIUM,
            ),
            SeverityThreshold(
                threshold=0.60,
                severity=RuleSeverity.HIGH,
            ),
        ),
    )


@pytest.fixture
def rule(rule_config):
    return FinancialExpensesToEbitdaRule(rule_config)


def make_position(
    *,
    ebitda: float | None,
    interest_expense: float | None,
) -> CreditPosition:
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=0.0,
        ebitda=ebitda,
        profit_loss=0.0,
        ebitda_margin=0.0,
        pfn_to_ebitda=0.0,
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
        (
            250_000,
            50_000,
            0.20,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.LOW,
        ),
        (
            250_000,
            100_000,
            0.40,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.MEDIUM,
        ),
        (
            250_000,
            150_000,
            0.60,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.HIGH,
        ),
        (
            250_000,
            200_000,
            0.80,
            RuleStatus.TRIGGERED,
            RuleSeverity.HIGH,
        ),
    ],
)
def test_interest_expense_to_ebitda_rule_evaluates_ratio(
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


@pytest.mark.parametrize(
    ("ebitda", "interest_expense"),
    [
        (None, 100_000),
        (250_000, None),
    ],
)
def test_interest_expense_to_ebitda_rule_is_not_evaluable_missing_data(
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


@pytest.mark.parametrize(
    ("ebitda", "interest_expense"),
    [
        (-50_000, 40_000),
        (0, 40_000),
    ],
)
def test_interest_expense_to_ebitda_rule_negative_ebitda_is_not_evaluable(
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

    assert result.reason is not None
    assert (
        "EBITDA is negative or zero"
        in result.reason
    )


def test_interest_expense_to_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="CUSTOM_RULE",
        rule_name="Custom rule",
        category=CATEGORY,
        threshold=1.00,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    )

    position = make_position(
        ebitda=250_000,
        interest_expense=200_000,
    )

    result = FinancialExpensesToEbitdaRule(config).evaluate(position)

    assert_result_metadata(result, config)

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.80
    assert result.severity == RuleSeverity.MEDIUM