from src.models.position import CreditPosition
from src.rules.financial_expenses_rules import FinancialExpensesToEbitdaRule


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

    rule = FinancialExpensesToEbitdaRule()

    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.triggered is True
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

    rule = FinancialExpensesToEbitdaRule()

    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.triggered is False
    assert result.value == 0.4
    assert result.threshold == 0.60


def test_interest_expense_to_ebitda_rule_with_negative_ebitda():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    rule = FinancialExpensesToEbitdaRule()

    result = rule.evaluate(position)

    assert result.rule_id == "R005"
    assert result.rule_name == "Interest expense to EBITDA"
    assert result.category == "profitability"
    assert result.triggered is False
    assert result.value is None
    assert result.threshold == 0.60