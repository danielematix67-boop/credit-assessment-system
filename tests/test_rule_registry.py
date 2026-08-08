from src.rules.registry import get_default_rules
from src.rules.revenue_rules import RevenueGrowthRule
from src.rules.profitability_rules import NegativeEbitdaRule
from src.rules.margin_rules import EbitdaMarginRule
from src.rules.leverage_rules import PfnToEbitdaRule
from src.rules.financial_expenses_rules import FinancialExpensesToEbitdaRule


def test_default_rules_registry():
    rules = get_default_rules()

    assert len(rules) == 5

    assert isinstance(rules[0], RevenueGrowthRule)
    assert isinstance(rules[1], NegativeEbitdaRule)
    assert isinstance(rules[2], EbitdaMarginRule)
    assert isinstance(rules[3], PfnToEbitdaRule)
    assert isinstance(rules[4], FinancialExpensesToEbitdaRule)