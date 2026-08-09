from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


DEFAULT_RULES = [
    RevenueGrowthRule(),
    NegativeEbitdaRule(),
    EbitdaMarginRule(),
    PfnToEbitdaRule(),
    FinancialExpensesToEbitdaRule(),
]

