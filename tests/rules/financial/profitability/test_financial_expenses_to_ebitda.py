import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.financial.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


RULE_ID = "TEST_RULE"
RULE_NAME = "Test interest expense to EBITDA"
CATEGORY = "test"
THRESHOLD = 0.60
SEVERITY = RuleSeverity.MEDIUM


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id=RULE_ID,
        rule_name=RULE_NAME,
        category=CATEGORY,
        threshold=THRESHOLD,
        severity=SEVERITY,
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
    assert result.severity == config.severity


@pytest.mark.parametrize(
    ("ebitda", "interest_expense", "expected_value"),
    [
        (250_000, 200_000, 0.80),
        (250_000, 100_000, 0.40),
    ],
)
def test_interest_expense_to_ebitda_rule_evaluates_ratio(
    rule,
    rule_config,
    ebitda,
    interest_expense,
    expected_value,
):
    position = make_position(
        ebitda=ebitda,
        interest_expense=interest_expense,
    )

    result = rule.evaluate(position)

    assert_result_metadata(result, rule_config)
    assert result.value == expected_value

    expected_status = (
        RuleStatus.TRIGGERED
        if expected_value >= rule_config.threshold
        else RuleStatus.NOT_TRIGGERED
    )

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("ebitda", "interest_expense"),
    [
        (-50_000, 40_000),
        (None, 100_000),
        (0, 40_000),
        (250_000, None),
    ],
)
def test_interest_expense_to_ebitda_rule_is_not_evaluable(
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


def test_interest_expense_to_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="CUSTOM_RULE",
        rule_name="Custom rule",
        category=CATEGORY,
        threshold=1.00,
        severity=RuleSeverity.HIGH,
    )

    position = make_position(
        ebitda=250_000,
        interest_expense=200_000,
    )

    result = FinancialExpensesToEbitdaRule(config).evaluate(position)

    assert_result_metadata(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.80