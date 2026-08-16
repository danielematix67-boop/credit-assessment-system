from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection


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
    assert all(
        config.severity_direction in SeverityDirection
        for config in configs
    )


def test_rule_config_loader_loads_expected_severity_directions():
    loader = RuleConfigLoader()

    configs = loader.load(RULES_CONFIG_PATH)

    configurations = {
        config.rule_id: config
        for config in configs
    }

    assert (
        configurations["R001"].severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )
    assert (
        configurations["R002"].severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )
    assert (
        configurations["R003"].severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )
    assert (
        configurations["R004"].severity_direction
        == SeverityDirection.HIGHER_IS_WORSE
    )
    assert (
        configurations["R005"].severity_direction
        == SeverityDirection.HIGHER_IS_WORSE
    )
    assert (
        configurations["R006"].severity_direction
        == SeverityDirection.HIGHER_IS_WORSE
    )
    assert (
        configurations["R007"].severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )


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
            severity_direction: LOWER_IS_WORSE

          - rule_id: R001
            rule_name: Rule one
            category: test
            threshold: 1.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE

          - rule_id: R002
            rule_name: Rule two
            category: test
            threshold: 2.0
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE
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
            severity_direction: LOWER_IS_WORSE
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
    assert (
        config.severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )
    assert config.severity_thresholds == ()


def test_rule_config_loader_loads_higher_is_worse_direction(
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R999
            rule_name: Test rule
            category: test
            threshold: 5.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    assert len(configs) == 1
    assert (
        configs[0].severity_direction
        == SeverityDirection.HIGHER_IS_WORSE
    )


def test_rule_config_loader_loads_lower_is_worse_direction(
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R999
            rule_name: Test rule
            category: test
            threshold: -0.10
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    assert len(configs) == 1
    assert (
        configs[0].severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )


def test_rule_config_loader_loads_severity_thresholds(tmp_path):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R004
            rule_name: PFN / EBITDA leverage
            category: leverage
            threshold: 5.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: 3.0
                severity: LOW
              - threshold: 5.0
                severity: MEDIUM
              - threshold: 7.0
                severity: HIGH
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    assert len(configs) == 1

    config = configs[0]

    assert config.rule_id == "R004"
    assert config.threshold == 5.0
    assert config.severity == RuleSeverity.HIGH
    assert (
        config.severity_direction
        == SeverityDirection.HIGHER_IS_WORSE
    )

    assert config.severity_thresholds == (
        SeverityThreshold(
            threshold=3.0,
            severity=RuleSeverity.LOW,
        ),
        SeverityThreshold(
            threshold=5.0,
            severity=RuleSeverity.MEDIUM,
        ),
        SeverityThreshold(
            threshold=7.0,
            severity=RuleSeverity.HIGH,
        ),
    )


def test_rule_config_loader_preserves_severity_threshold_order(
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R999
            rule_name: Test rule
            category: test
            threshold: 10.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: 10.0
                severity: HIGH
              - threshold: 5.0
                severity: MEDIUM
              - threshold: 2.0
                severity: LOW
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    thresholds = configs[0].severity_thresholds

    assert [item.threshold for item in thresholds] == [
        10.0,
        5.0,
        2.0,
    ]

    assert [item.severity for item in thresholds] == [
        RuleSeverity.HIGH,
        RuleSeverity.MEDIUM,
        RuleSeverity.LOW,
    ]


def test_rule_config_loader_raises_when_file_does_not_exist(
    tmp_path,
):
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
            severity_direction: LOWER_IS_WORSE
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


def test_rule_config_loader_raises_when_rules_section_is_missing(
    tmp_path,
):
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


def test_rule_config_loader_raises_when_required_field_is_missing(
    tmp_path,
):
    config_path = tmp_path / "missing_field.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
            severity: MEDIUM
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_severity_is_invalid(
    tmp_path,
):
    config_path = tmp_path / "invalid_severity.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
            severity: INVALID
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid severity for rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_raises_when_threshold_is_not_numeric(
    tmp_path,
):
    config_path = tmp_path / "invalid_threshold.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: not-a-number
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid threshold for rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_raises_when_rule_ids_are_duplicated(
    tmp_path,
):
    config_path = tmp_path / "duplicate_rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Revenue growth deterioration
            category: revenue
            threshold: -0.10
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE

          - rule_id: R001
            rule_name: Another rule
            category: revenue
            threshold: -0.20
            severity: LOW
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_severity_direction_is_invalid(
    tmp_path,
):
    config_path = tmp_path / "invalid_severity_direction.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Test rule
            category: test
            threshold: 5.0
            severity: HIGH
            severity_direction: INVALID
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid severity direction for rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_raises_when_severity_thresholds_are_invalid(
    tmp_path,
):
    config_path = tmp_path / "invalid_severity_thresholds.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Test rule
            category: test
            threshold: 5.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: invalid
                severity: LOW
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid severity threshold for rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_raises_when_severity_threshold_severity_is_invalid(
    tmp_path,
):
    config_path = tmp_path / "invalid_severity_threshold_severity.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Test rule
            category: test
            threshold: 5.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: 3.0
                severity: INVALID
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    with pytest.raises(
        ValueError,
        match="Invalid severity for severity threshold of rule_id: R001",
    ):
        loader.load(config_path)


def test_rule_config_loader_accepts_rules_without_severity_thresholds(
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Test rule
            category: test
            threshold: 5.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
        """,
        encoding="utf-8",
    )

    loader = RuleConfigLoader()

    configs = loader.load(config_path)

    assert len(configs) == 1
    assert configs[0].severity_thresholds == ()
