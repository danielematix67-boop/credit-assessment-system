from pathlib import Path

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.registry import build_rules, get_default_rules

FINANCIAL_RULES_PATH = Path("config/financial_analysis_rules.yaml")
ALL_RULES_PATH = Path("config")


def test_default_rule_configuration_uses_financial_rule_catalog() -> None:
    configs = RuleConfigLoader().load(FINANCIAL_RULES_PATH)
    rules = get_default_rules()
    financial_rule_ids = {config.rule_id for config in configs}
    default_rule_ids = {rule.config.rule_id for rule in rules}

    assert financial_rule_ids <= default_rule_ids


def test_rule_configuration_loads_all_rule_catalogs() -> None:
    configs = RuleConfigLoader().load(ALL_RULES_PATH)
    rule_ids = [config.rule_id for config in configs]

    assert rule_ids
    assert len(rule_ids) == len(set(rule_ids))


def test_all_rule_catalog_entries_have_registered_implementations() -> None:
    configs = RuleConfigLoader().load(ALL_RULES_PATH)
    rules = build_rules(configs)

    assert {rule.config.rule_id for rule in rules} == {
        config.rule_id for config in configs
    }
    assert len(rules) == len(configs)
