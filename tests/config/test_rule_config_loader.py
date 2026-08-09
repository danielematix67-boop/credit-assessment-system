from pathlib import Path

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


RULES_CONFIG_PATH = Path("config/rules.yaml")


def test_rule_config_loader_loads_all_rules():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert len(configs) == 5


def test_rule_config_loader_loads_rule_ids():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert [config.rule_id for config in configs] == [
        "R001",
        "R002",
        "R003",
        "R004",
        "R005",
    ]


def test_rule_config_loader_loads_rule_configuration():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    config = {item.rule_id: item for item in configs}

    assert config["R001"].rule_name == "Revenue growth deterioration"
    assert config["R001"].category == "revenue"
    assert config["R001"].threshold == -0.10
    assert config["R001"].severity == RuleSeverity.MEDIUM

    assert config["R002"].rule_name == "Negative EBITDA"
    assert config["R002"].category == "profitability"
    assert config["R002"].threshold == 0.0
    assert config["R002"].severity == RuleSeverity.HIGH

    assert config["R003"].rule_name == "EBITDA margin deterioration"
    assert config["R003"].category == "profitability"
    assert config["R003"].threshold == 0.0
    assert config["R003"].severity == RuleSeverity.MEDIUM

    assert config["R004"].rule_name == "PFN / EBITDA leverage"
    assert config["R004"].category == "leverage"
    assert config["R004"].threshold == 5.0
    assert config["R004"].severity == RuleSeverity.HIGH

    assert config["R005"].rule_name == "Interest expense to EBITDA"
    assert config["R005"].category == "profitability"
    assert config["R005"].threshold == 0.60
    assert config["R005"].severity == RuleSeverity.MEDIUM


def test_rule_config_loader_preserves_rule_order():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert [config.rule_id for config in configs] == [
        "R001",
        "R002",
        "R003",
        "R004",
        "R005",
    ]


def test_rule_config_loader_returns_rule_config_objects():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert all(
        isinstance(config, RuleConfig)
        for config in configs
    )
