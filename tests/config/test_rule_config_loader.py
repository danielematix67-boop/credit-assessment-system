from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


RULES_CONFIG_PATH = Path("config/rules.yaml")


def test_rule_config_loader_loads_rules():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert configs
    assert all(
        isinstance(config, RuleConfig)
        for config in configs
    )


def test_rule_config_loader_loads_unique_rule_ids():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    rule_ids = [config.rule_id for config in configs]

    assert len(rule_ids) == len(set(rule_ids))


def test_rule_config_loader_loads_complete_configurations():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    assert all(config.rule_id for config in configs)
    assert all(config.rule_name for config in configs)
    assert all(config.category for config in configs)
    assert all(config.severity in RuleSeverity for config in configs)


def test_rule_config_loader_preserves_input_order(tmp_path):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R003
            rule_name: Rule three
            category: test
            threshold: 3.0
            severity: LOW

          - rule_id: R001
            rule_name: Rule one
            category: test
            threshold: 1.0
            severity: HIGH

          - rule_id: R002
            rule_name: Rule two
            category: test
            threshold: 2.0
            severity: MEDIUM
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    assert [config.rule_id for config in configs] == [
        "R003",
        "R001",
        "R002",
    ]


def test_rule_config_loader_loads_configuration_values(tmp_path):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R999
            rule_name: Test rule
            category: test_category
            threshold: 0.30
            severity: MEDIUM
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    assert len(configs) == 1

    config = configs[0]

    assert config.rule_id == "R999"
    assert config.rule_name == "Test rule"
    assert config.category == "test_category"
    assert config.threshold == 0.30
    assert config.severity == RuleSeverity.MEDIUM


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
