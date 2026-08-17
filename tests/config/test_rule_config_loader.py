from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection


RULES_CONFIG_PATH = Path("config/rules.yaml")


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def loader():
    return RuleConfigLoader()


# ============================================================
# Valid configuration
# ============================================================


def test_rule_config_loader_returns_rule_configs(loader):
    configs = loader.load(RULES_CONFIG_PATH)

    assert configs
    assert all(isinstance(config, RuleConfig) for config in configs)


def test_rule_config_loader_returns_unique_rule_ids(loader):
    configs = loader.load(RULES_CONFIG_PATH)

    rule_ids = [config.rule_id for config in configs]

    assert len(rule_ids) == len(set(rule_ids))


def test_rule_config_loader_returns_complete_configurations(loader):
    configs = loader.load(RULES_CONFIG_PATH)

    for config in configs:
        assert config.rule_id
        assert config.rule_name
        assert config.category
        assert isinstance(config.threshold, (int, float))
        assert isinstance(config.severity, RuleSeverity)
        assert isinstance(
            config.severity_direction,
            SeverityDirection,
        )


def test_rule_config_loader_returns_valid_severity_thresholds(loader):
    configs = loader.load(RULES_CONFIG_PATH)

    for config in configs:
        assert isinstance(
            config.severity_thresholds,
            tuple,
        )

        for severity_threshold in config.severity_thresholds:
            assert isinstance(
                severity_threshold,
                SeverityThreshold,
            )
            assert isinstance(
                severity_threshold.threshold,
                (int, float),
            )
            assert isinstance(
                severity_threshold.severity,
                RuleSeverity,
            )


def test_rule_config_loader_preserves_number_of_configured_rules(
    loader,
):
    configs = loader.load(RULES_CONFIG_PATH)

    assert len(configs) > 0


# ============================================================
# Input order
# ============================================================


def test_rule_config_loader_preserves_input_order(
    loader,
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: first
            rule_name: First rule
            category: test
            threshold: 1.0
            severity: LOW
            severity_direction: LOWER_IS_WORSE

          - rule_id: second
            rule_name: Second rule
            category: test
            threshold: 2.0
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE

          - rule_id: third
            rule_name: Third rule
            category: test
            threshold: 3.0
            severity: HIGH
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    configs = loader.load(config_path)

    assert [config.rule_id for config in configs] == [
        "first",
        "second",
        "third",
    ]


# ============================================================
# Configuration values
# ============================================================


def test_rule_config_loader_preserves_configuration_values(
    loader,
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test_category
            threshold: 0.30
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    configs = loader.load(config_path)

    assert len(configs) == 1

    config = configs[0]

    assert config.rule_id == "test_rule"
    assert config.rule_name == "Test rule"
    assert config.category == "test_category"
    assert config.threshold == pytest.approx(0.30)
    assert config.severity == RuleSeverity.MEDIUM
    assert (
        config.severity_direction
        == SeverityDirection.LOWER_IS_WORSE
    )
    assert config.severity_thresholds == ()


@pytest.mark.parametrize(
    "direction",
    list(SeverityDirection),
)
def test_rule_config_loader_supports_valid_severity_directions(
    loader,
    tmp_path,
    direction,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        f"""
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: {direction.name}
        """,
        encoding="utf-8",
    )

    configs = loader.load(config_path)

    assert len(configs) == 1
    assert configs[0].severity_direction == direction


# ============================================================
# Severity thresholds
# ============================================================


def test_rule_config_loader_loads_severity_thresholds(
    loader,
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 5.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: 1.0
                severity: LOW
              - threshold: 5.0
                severity: MEDIUM
              - threshold: 10.0
                severity: HIGH
        """,
        encoding="utf-8",
    )

    configs = loader.load(config_path)

    assert len(configs) == 1

    thresholds = configs[0].severity_thresholds

    assert len(thresholds) == 3
    assert all(
        isinstance(item, SeverityThreshold)
        for item in thresholds
    )


def test_rule_config_loader_preserves_severity_threshold_order(
    loader,
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
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


def test_rule_config_loader_accepts_configuration_without_thresholds(
    loader,
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
        """,
        encoding="utf-8",
    )

    configs = loader.load(config_path)

    assert len(configs) == 1
    assert configs[0].severity_thresholds == ()


# ============================================================
# File errors
# ============================================================


def test_rule_config_loader_raises_for_missing_file(
    loader,
    tmp_path,
):
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        loader.load(missing_path)


def test_rule_config_loader_raises_for_invalid_yaml(
    loader,
    tmp_path,
):
    config_path = tmp_path / "invalid.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE
          invalid yaml: [
        """,
        encoding="utf-8",
    )

    with pytest.raises(Exception):
        loader.load(config_path)


def test_rule_config_loader_raises_for_empty_file(
    loader,
    tmp_path,
):
    config_path = tmp_path / "empty.yaml"

    config_path.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_rules_section_is_missing(
    loader,
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

    with pytest.raises(ValueError):
        loader.load(config_path)


# ============================================================
# Validation errors
# ============================================================


def test_rule_config_loader_rejects_missing_required_field(
    loader,
    tmp_path,
):
    config_path = tmp_path / "missing_field.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_invalid_severity(
    loader,
    tmp_path,
):
    config_path = tmp_path / "invalid_severity.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: INVALID
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_non_numeric_threshold(
    loader,
    tmp_path,
):
    config_path = tmp_path / "invalid_threshold.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: not_numeric
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_duplicate_rule_ids(
    loader,
    tmp_path,
):
    config_path = tmp_path / "duplicate_rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: duplicate
            rule_name: First rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE

          - rule_id: duplicate
            rule_name: Second rule
            category: test
            threshold: 2.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_invalid_severity_direction(
    loader,
    tmp_path,
):
    config_path = tmp_path / "invalid_direction.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: INVALID
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_invalid_severity_threshold(
    loader,
    tmp_path,
):
    config_path = tmp_path / "invalid_severity_threshold.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: invalid
                severity: LOW
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_invalid_threshold_severity(
    loader,
    tmp_path,
):
    config_path = tmp_path / "invalid_threshold_severity.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: 2.0
                severity: INVALID
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        loader.load(config_path)