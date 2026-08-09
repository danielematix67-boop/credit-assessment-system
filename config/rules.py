from src.rules.base.config import RuleConfig

from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


R001_CONFIG = RuleConfig(
    rule_id="R001",
    rule_name="Revenue deterioration",
    category="revenue",
    threshold=-0.10,
)

R002_CONFIG = RuleConfig(
    rule_id="R002",
    rule_name="Negative EBITDA",
    category="profitability",
    threshold=0,
)

R003_CONFIG = RuleConfig(
    rule_id="R003",
    rule_name="EBITDA margin deterioration",
    category="profitability",
    threshold=0.0,
)

R004_CONFIG = RuleConfig(
    rule_id="R004",
    rule_name="PFN / EBITDA leverage",
    category="leverage",
    threshold=5.0,
)

R005_CONFIG = RuleConfig(
    rule_id="R005",
    rule_name="Interest expense to EBITDA",
    category="profitability",
    threshold=0.60,
)


DEFAULT_RULES = [
    RevenueGrowthRule(R001_CONFIG),
    NegativeEbitdaRule(R002_CONFIG),
    EbitdaMarginRule(R003_CONFIG),
    PfnToEbitdaRule(R004_CONFIG),
    FinancialExpensesToEbitdaRule(R005_CONFIG),
]
