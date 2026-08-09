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
    assert rules[0].config.rule_id == "R001"
    assert rules[0].config.category == "revenue"
    assert rules[0].config.threshold == -0.10

    assert isinstance(rules[1], NegativeEbitdaRule)
    assert rules[1].config.rule_id == "R002"
    assert rules[1].config.category == "profitability"
    assert rules[1].config.threshold == 0.0

    assert isinstance(rules[2], EbitdaMarginRule)
    assert rules[2].config.rule_id == "R003"
    assert rules[2].config.category == "profitability"
    assert rules[2].config.threshold == 0.0

    assert isinstance(rules[3], PfnToEbitdaRule)
    assert rules[3].config.rule_id == "R004"
    assert rules[3].config.category == "leverage"
    assert rules[3].config.threshold == 5.0

    assert isinstance(rules[4], FinancialExpensesToEbitdaRule)
    assert rules[4].config.rule_id == "R005"
    assert rules[4].config.category == "profitability"
    assert rules[4].config.threshold == 0.60
