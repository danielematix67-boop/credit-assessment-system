from src.rules.financial_expenses_rules import FinancialExpensesToEbitdaRule
from src.rules.revenue_rules import RevenueGrowthRule
from src.rules.profitability_rules import NegativeEbitdaRule
from src.rules.margin_rules import EbitdaMarginRule
from src.rules.leverage_rules import PfnToEbitdaRule


DEFAULT_RULES = [
    RevenueGrowthRule(),
    NegativeEbitdaRule(),
    EbitdaMarginRule(),
    PfnToEbitdaRule(),
    FinancialExpensesToEbitdaRule(),
]