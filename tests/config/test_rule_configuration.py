from pathlib import Path

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.registry import build_rules, get_default_rules

EXPECTED_RULE_IDS = {
    "CP001",
    "CP002",
    "CP003",
    "CP004",
    "R001",
    "R002",
    "R003",
    "R004",
    "R005",
    "R006",
    "R007",
    "B001",
    "B002",
    "B003",
    "B004",
    "DS001",
    "DS002",
    "DS003",
}


def test_default_rule_configuration_uses_core_rule_engine_catalog() -> None:
    rules = get_default_rules()
    rule_ids = {rule.config.rule_id for rule in rules}

    assert rule_ids == {
        "R001",
        "R002",
        "R003",
        "R004",
        "R005",
        "R006",
        "R007",
    }


def test_rule_configuration_loads_all_rule_catalogs() -> None:
    configs = RuleConfigLoader().load(Path("config"))
    rule_ids = {config.rule_id for config in configs}

    assert rule_ids == EXPECTED_RULE_IDS
    assert len(configs) == len(EXPECTED_RULE_IDS)


def test_all_rule_catalog_entries_have_registered_implementations() -> None:
    configs = RuleConfigLoader().load(Path("config"))
    rules = build_rules(configs)

    assert {rule.config.rule_id for rule in rules} == EXPECTED_RULE_IDS
