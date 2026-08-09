from src.rules.registry import get_default_rules

from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


def test_default_rules_registry():
    rules = get_default_rules()

    assert len(rules) == 5

    assert isinstance(rules[0], RevenueGrowthRule)
    assert isinstance(rules[1], NegativeEbitdaRule)
    assert isinstance(rules[2], EbitdaMarginRule)
    assert isinstance(rules[3], PfnToEbitdaRule)
    assert isinstance(rules[4], FinancialExpensesToEbitdaRule)
