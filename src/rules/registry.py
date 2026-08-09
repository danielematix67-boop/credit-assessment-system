from pathlib import Path

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.rule import Rule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)
from src.rules.revenue.revenue_growth import RevenueGrowthRule


RULES_CONFIG_PATH = Path("config/rules.yaml")


_RULE_FACTORIES = {
    "R001": RevenueGrowthRule,
    "R002": NegativeEbitdaRule,
    "R003": EbitdaMarginRule,
    "R004": PfnToEbitdaRule,
    "R005": FinancialExpensesToEbitdaRule,
}


def get_default_rules() -> list[Rule]:
    loader = RuleConfigLoader()
    configs = loader.load(RULES_CONFIG_PATH)

    return [
        _RULE_FACTORIES[config.rule_id](config)
        for config in configs
    ]