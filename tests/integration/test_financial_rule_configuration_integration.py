from pathlib import Path

from src.config.rule_config_loader import RuleConfigLoader
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.discovery import discover_rules

RULES_CONFIG_PATH = Path("config/financial_analysis_rules.yaml")
EXPECTED_RULE_IDS = [
    "R001",
    "R002",
    "R003",
    "R004",
    "R005",
    "R006",
    "R007",
]


def test_financial_configuration_matches_discovered_rule_registry():
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    discover_rules()

    configured_rule_ids = [config.rule_id for config in configs]

    assert configured_rule_ids == EXPECTED_RULE_IDS
    assert set(configured_rule_ids) <= set(Rule._registry)


def test_financial_configuration_rules_are_instantiable_and_evaluable():
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    discover_rules()
    position = CreditPosition(
        position_id="integration-test",
        revenue_growth=0.05,
        ebitda=100.0,
        ebitda_margin=0.10,
        nfp_to_ebitda=4.0,
        interest_expense=50.0,
        change_in_finished_goods_inventory=20.0,
    )

    results = []
    for config in configs:
        rule_class = Rule.get_registered_rule(config.rule_id)
        rule = rule_class(config)
        results.append(rule.evaluate(position))

    assert [result.rule_id for result in results] == EXPECTED_RULE_IDS
    assert all(result.status != RuleStatus.NOT_EVALUABLE for result in results)
    assert all(result.value is not None for result in results)


def test_financial_configuration_preserves_configured_calculation_semantics():
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    config_by_id = {config.rule_id: config for config in configs}

    assert config_by_id["R001"].calculation == "direct"
    assert config_by_id["R002"].calculation == "direct"
    assert config_by_id["R003"].calculation == "direct"
    assert config_by_id["R004"].calculation == "direct"
    assert config_by_id["R005"].calculation == "ratio"
    assert config_by_id["R006"].calculation == "ratio"
    assert config_by_id["R007"].calculation == "ratio"
