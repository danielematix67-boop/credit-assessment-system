from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


def test_interest_expense_to_ebitda_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=200000,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == 0.8
    assert result.threshold == 0.60


def test_interest_expense_to_ebitda_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=100000,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.4
    assert result.threshold == 0.60


def test_interest_expense_to_ebitda_rule_not_evaluable_with_negative_ebitda():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.60


def test_interest_expense_to_ebitda_rule_not_evaluable_when_interest_expense_none():
    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=None,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.60


def test_interest_expense_to_ebitda_rule_not_evaluable_when_ebitda_none():
    position = CreditPosition(
        position_id="POS005",
        revenue_growth=0.05,
        ebitda=None,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=100000,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.60


def test_interest_expense_to_ebitda_rule_not_evaluable_with_zero_ebitda():
    position = CreditPosition(
        position_id="POS006",
        revenue_growth=0.05,
        ebitda=0,
        profit_loss=-50000,
        ebitda_margin=0.0,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.60
