from src.config.rule_config_loader import RuleConfigLoader
from src.config.rule_configuration import RuleConfiguration
from src.rules.base.config import RuleConfig
from src.rules.base.rule import Rule
from src.rules.discovery import discover_rules


def build_rules(configs: list[RuleConfig]) -> list[Rule]:
    discover_rules()

    rules = []

    for config in configs:
        rule_class = Rule.get_registered_rule(config.rule_id)
        rules.append(rule_class(config))

    return rules


def get_default_rules(
    configuration: RuleConfiguration | None = None,
) -> list[Rule]:
    configuration = configuration or RuleConfiguration.default()

    loader = RuleConfigLoader()
    configs = loader.load(configuration.rules_path)

    return build_rules(configs)