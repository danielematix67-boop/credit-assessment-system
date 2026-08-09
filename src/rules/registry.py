from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.profitability.financial_expenses_to_ebitda import FinancialExpensesToEbitdaRule
from src.rules.base.rule import Rule

# The registry defines the default set and execution order of business rules.
# Adding a new default rule requires registering its rule class here.
# The registry should not contain the implementation of the rules themselves.


def get_default_rules() -> list[Rule]:
    return [
        RevenueGrowthRule(),
        NegativeEbitdaRule(),
        EbitdaMarginRule(),
        PfnToEbitdaRule(),
        FinancialExpensesToEbitdaRule(),
    ]