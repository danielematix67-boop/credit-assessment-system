from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.registry import build_rules
from src.rules.revenue.revenue_growth import RevenueGrowthRule


RULES_CONFIG_PATH = Path("config/rules.yaml")


def test_rule_config_loader_loads_all_rules():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert len(configs) == 6


def test_rule_config_loader_loads_rule_ids():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert [config.rule_id for config in configs] == [
        "R001",
        "R002",
        "R003",
        "R004",
        "R005",
        "R006",
    ]


def test_rule_config_loader_loads_rule_configuration():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    config = {item.rule_id: item for item in configs}

    # R001 - Revenue growth deterioration
    assert config["R001"].rule_name == "Revenue growth deterioration"
    assert config["R001"].category == "revenue"
    assert config["R001"].threshold == -0.10
    assert config["R001"].severity == RuleSeverity.MEDIUM

    # R002 - Negative EBITDA
    assert config["R002"].rule_name == "Negative EBITDA"
    assert config["R002"].category == "profitability"
    assert config["R002"].threshold == 0.0
    assert config["R002"].severity == RuleSeverity.HIGH

    # R003 - EBITDA margin deterioration
    assert config["R003"].rule_name == "EBITDA margin deterioration"
    assert config["R003"].category == "profitability"
    assert config["R003"].threshold == 0.0
    assert config["R003"].severity == RuleSeverity.MEDIUM

    # R004 - PFN / EBITDA leverage
    assert config["R004"].rule_name == "PFN / EBITDA leverage"
    assert config["R004"].category == "leverage"
    assert config["R004"].threshold == 5.0
    assert config["R004"].severity == RuleSeverity.HIGH

    # R005 - Interest expense to EBITDA
    assert config["R005"].rule_name == "Interest expense to EBITDA"
    assert config["R005"].category == "profitability"
    assert config["R005"].threshold == 0.60
    assert config["R005"].severity == RuleSeverity.MEDIUM

    # R006 - EBITDA materially supported by finished goods inventory increase
    assert (
        config["R006"].rule_name
        == "EBITDA materially supported by finished goods inventory increase"
    )
    assert config["R006"].category == "profitability_quality"
    assert config["R006"].threshold == 0.30
    assert config["R006"].severity == RuleSeverity.MEDIUM


def test_rule_config_loader_preserves_rule_order():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert [config.rule_id for config in configs] == [
        "R001",
        "R002",
        "R003",
        "R004",
        "R005",
        "R006",
    ]


def test_rule_config_loader_returns_rule_config_objects():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert all(
        isinstance(config, RuleConfig)
        for config in configs
    )


def test_rule_config_loader_raises_when_file_does_not_exist(tmp_path):
    loader = RuleConfigLoader()

    missing_path = tmp_path / "missing_rules.yaml"

    with pytest.raises(FileNotFoundError):
        loader.load(missing_path)


def test_rule_config_loader_raises_when_yaml_is_invalid(tmp_path):
    config_path = tmp_path / "invalid_rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
            severity: MEDIUM
          invalid yaml: [
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(Exception):
        loader.load(config_path)


def test_rule_config_loader_raises_when_yaml_is_empty(tmp_path):
    config_path = tmp_path / "empty_rules.yaml"

    config_path.write_text(
        "",
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_rules_section_is_missing(tmp_path):
    config_path = tmp_path / "missing_rules.yaml"

    config_path.write_text(
        """
        configuration:
          enabled: true
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_required_field_is_missing(tmp_path):
    config_path = tmp_path / "missing_field.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_severity_is_invalid(tmp_path):
    config_path = tmp_path / "invalid_severity.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
            severity: INVALID
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid severity for rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_raises_when_threshold_is_not_numeric(tmp_path):
    config_path = tmp_path / "invalid_threshold.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: not-a-number
            severity: MEDIUM
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid threshold for rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_raises_when_rule_ids_are_duplicated(tmp_path):
    config_path = tmp_path / "duplicate_rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
            severity: MEDIUM

          - rule_id: R001
            rule_name: Another rule
            category: revenue
            threshold: -0.20
            severity: LOW
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_build_rules_uses_configuration_threshold():
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.20,
        severity=RuleSeverity.MEDIUM,
    )

    rules = build_rules([config])

    assert len(rules) == 1
    assert isinstance(rules[0], RevenueGrowthRule)

    assert rules[0].config.rule_id == "R001"
    assert rules[0].config.threshold == -0.20
    assert rules[0].config.severity == RuleSeverity.MEDIUM
