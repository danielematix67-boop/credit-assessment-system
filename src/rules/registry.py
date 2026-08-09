from src.config.rule_config_loader import RuleConfigLoader
from src.config.rule_configuration import RuleConfiguration
from src.rules.base.config import RuleConfig
from src.rules.base.rule import Rule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)
from src.rules.revenue.revenue_growth import RevenueGrowthRule


_RULE_FACTORIES = {
    "R001": RevenueGrowthRule,
    "R002": NegativeEbitdaRule,
    "R003": EbitdaMarginRule,
    "R004": PfnToEbitdaRule,
    "R005": FinancialExpensesToEbitdaRule,
}


def build_rules(configs: list[RuleConfig]) -> list[Rule]:
    rules = []

    for config in configs:
        factory = _RULE_FACTORIES.get(config.rule_id)

        if factory is None:
            raise ValueError(f"Unknown rule_id: {config.rule_id}")

        rules.append(factory(config))

    return rules


def get_default_rules(
    configuration: RuleConfiguration | None = None,
) -> list[Rule]:
    configuration = configuration or RuleConfiguration.default()

    loader = RuleConfigLoader()
    configs = loader.load(configuration.rules_path)

    return build_rules(configs)
