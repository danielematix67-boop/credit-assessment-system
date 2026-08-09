from src.rules.base.config import RuleConfig
from src.rules.base.rule import Rule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)
from src.rules.revenue.revenue_growth import RevenueGrowthRule


# The registry defines the default set and execution order of business rules.
#
# Adding a new default rule requires registering its configuration and rule
# class here.
#
# The registry should not contain the implementation of the rules themselves.


def get_default_rules() -> list[Rule]:
    return [
        RevenueGrowthRule(
            RuleConfig(
                rule_id="R001",
                rule_name="Revenue deterioration",
                category="revenue",
                threshold=-0.10,
            )
        ),
        NegativeEbitdaRule(
            RuleConfig(
                rule_id="R002",
                rule_name="Negative EBITDA",
                category="profitability",
                threshold=0,
            )
        ),
        EbitdaMarginRule(
            RuleConfig(
                rule_id="R003",
                rule_name="EBITDA margin deterioration",
                category="profitability",
                threshold=0.0,
            )
        ),
        PfnToEbitdaRule(
            RuleConfig(
                rule_id="R004",
                rule_name="PFN / EBITDA leverage",
                category="leverage",
                threshold=5.0,
            )
        ),
        FinancialExpensesToEbitdaRule(
            RuleConfig(
                rule_id="R005",
                rule_name="Interest expense to EBITDA",
                category="profitability",
                threshold=0.60,
            )
        ),
    ]
