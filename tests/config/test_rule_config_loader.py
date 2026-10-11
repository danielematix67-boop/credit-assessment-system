from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection

RULES_CONFIG_PATH = Path("config/financial_analysis_rules.yaml")


@pytest.fixture
def loader():
    return RuleConfigLoader()


def test_rule_config_loader_returns_rule_configs(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    assert configs
    assert all(isinstance(config, RuleConfig) for config in configs)


def test_rule_config_loader_returns_unique_rule_ids(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    rule_ids = [config.rule_id for config in configs]
    assert len(rule_ids) == len(set(rule_ids))


def test_financial_configuration_contains_all_configured_rules(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    assert configs
    assert all(config.rule_id.startswith("R") for config in configs)


def test_financial_configuration_input_fields_match_position_model(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    position_fields = set(CreditPosition.__dataclass_fields__)

    for config in configs:
        fields = set(config.input_fields)
        if config.input_field:
            fields.add(config.input_field)

        assert not (config.input_field and config.input_fields), (
            f"{config.rule_id} must use input_field or input_fields, not both"
        )
        assert fields <= position_fields, (
            f"{config.rule_id} references unknown CreditPosition fields: "
            f"{sorted(fields - position_fields)}"
        )


def test_financial_configuration_declares_input_fields_consistently(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    assert all(
        isinstance(config.input_field, str)
        and isinstance(config.input_fields, tuple)
        for config in configs
    )
    assert any(config.input_field for config in configs)
    assert any(config.input_fields for config in configs)


def test_financial_configuration_contains_comment_templates(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    assert all(config.comment_template for config in configs)


def test_rule_config_loader_returns_complete_configurations(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    for config in configs:
        assert config.rule_id
        assert config.rule_name
        assert config.category
        assert isinstance(config.threshold, (int, float))
        assert isinstance(config.severity, RuleSeverity)
        assert isinstance(config.severity_direction, SeverityDirection)


def test_rule_config_loader_returns_valid_severity_thresholds(loader):
    configs = loader.load(RULES_CONFIG_PATH)
    for config in configs:
        assert isinstance(config.severity_thresholds, tuple)
        for severity_threshold in config.severity_thresholds:
            assert isinstance(severity_threshold, SeverityThreshold)
            assert isinstance(severity_threshold.threshold, (int, float))
            assert isinstance(severity_threshold.severity, RuleSeverity)


def test_rule_config_loader_preserves_input_order(loader, tmp_path):
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
            trigger_operator: GT
          - rule_id: second
            rule_name: Second rule
            category: test
            threshold: 2.0
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE
            trigger_operator: GT
        """,
        encoding="utf-8",
    )
    configs = loader.load(config_path)
    assert [config.rule_id for config in configs] == ["first", "second"]


def test_rule_config_loader_preserves_configuration_values(loader, tmp_path):
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
            input_field: test_value
            trigger_operator: LTE
            comment_template: 'Configured value: {value}.'
        """,
        encoding="utf-8",
    )
    config = loader.load(config_path)[0]
    assert config.threshold == pytest.approx(0.30)
    assert config.input_field == "test_value"
    assert config.trigger_operator == "LTE"
    assert config.calculation == "direct"
    assert config.comment_template == "Configured value: {value}."


@pytest.mark.parametrize("direction", list(SeverityDirection))
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
            trigger_operator: GT
        """,
        encoding="utf-8",
    )
    assert loader.load(config_path)[0].severity_direction == direction


@pytest.mark.parametrize("operator", ["GT", "GTE", "LT", "LTE"])
def test_rule_config_loader_supports_valid_trigger_operators(
    loader,
    tmp_path,
    operator,
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
            severity_direction: HIGHER_IS_WORSE
            trigger_operator: {operator}
        """,
        encoding="utf-8",
    )
    assert loader.load(config_path)[0].trigger_operator == operator


@pytest.mark.parametrize("calculation", ["direct", "ratio", "difference"])
def test_rule_config_loader_supports_valid_calculations(
    loader,
    tmp_path,
    calculation,
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
            severity_direction: HIGHER_IS_WORSE
            trigger_operator: GT
            calculation: {calculation}
        """,
        encoding="utf-8",
    )
    assert loader.load(config_path)[0].calculation == calculation


def test_rule_config_loader_rejects_invalid_trigger_operator(loader, tmp_path):
    config_path = tmp_path / "invalid_operator.yaml"
    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE
            trigger_operator: BETWEEN
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="trigger_operator"):
        loader.load(config_path)


def test_rule_config_loader_rejects_invalid_calculation(loader, tmp_path):
    config_path = tmp_path / "invalid_calculation.yaml"
    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE
            trigger_operator: GT
            calculation: average
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="calculation"):
        loader.load(config_path)


def test_rule_config_loader_normalizes_operator_and_calculation(
    loader,
    tmp_path,
):
    config_path = tmp_path / "normalized.yaml"
    config_path.write_text(
        """
        rules:
          - rule_id: test_rule
            rule_name: Test rule
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE
            trigger_operator:  lt
            calculation:  RATIO
        """,
        encoding="utf-8",
    )
    config = loader.load(config_path)[0]
    assert config.trigger_operator == "LT"
    assert config.calculation == "ratio"


def test_rule_config_loader_raises_for_missing_file(loader, tmp_path):
    with pytest.raises(FileNotFoundError):
        loader.load(tmp_path / "missing.yaml")


def test_rule_config_loader_raises_for_empty_file(loader, tmp_path):
    config_path = tmp_path / "empty.yaml"
    config_path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_raises_when_rules_section_is_missing(loader, tmp_path):
    config_path = tmp_path / "missing_rules.yaml"
    config_path.write_text("configuration:\n  enabled: true\n", encoding="utf-8")
    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_missing_required_field(loader, tmp_path):
    config_path = tmp_path / "missing_field.yaml"
    config_path.write_text(
        "rules:\n"
        "  - rule_id: test_rule\n"
        "    rule_name: Test\n"
        "    category: test\n"
        "    threshold: 1.0\n"
        "    severity: MEDIUM\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        loader.load(config_path)


def test_rule_config_loader_rejects_duplicate_rule_ids(loader, tmp_path):
    config_path = tmp_path / "duplicate.yaml"
    config_path.write_text(
        """
        rules:
          - rule_id: duplicate
            rule_name: First
            category: test
            threshold: 1.0
            severity: MEDIUM
            severity_direction: LOWER_IS_WORSE
            trigger_operator: GT
          - rule_id: duplicate
            rule_name: Second
            category: test
            threshold: 2.0
            severity: HIGH
            severity_direction: HIGHER_IS_WORSE
            trigger_operator: GT
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        loader.load(config_path)
