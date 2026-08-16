from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.severity import RuleSeverity


RULES_CONFIG_PATH = Path("config/rules.yaml")


@pytest.fixture
def rule_configs():
    loader = RuleConfigLoader()

    return {
        config.rule_id: config
        for config in loader.load(RULES_CONFIG_PATH)
    }


@pytest.mark.parametrize(
    "rule_id, expected_threshold, expected_severity, expected_direction, expected_thresholds",
    [
        (
            "R001",
            -0.10,
            RuleSeverity.MEDIUM,
            "LOWER_IS_WORSE",
            (
                (-0.10, RuleSeverity.MEDIUM),
                (-0.30, RuleSeverity.HIGH),
            ),
        ),
        (
            "R002",
            0.0,
            RuleSeverity.HIGH,
            "LOWER_IS_WORSE",
            (),
        ),
        (
            "R003",
            0.0,
            RuleSeverity.MEDIUM,
            "LOWER_IS_WORSE",
            (
                (0.0, RuleSeverity.MEDIUM),
                (-0.10, RuleSeverity.HIGH),
            ),
        ),
        (
            "R004",
            5.0,
            RuleSeverity.MEDIUM,
            "HIGHER_IS_WORSE",
            (
                (5.0, RuleSeverity.MEDIUM),
                (7.0, RuleSeverity.HIGH),
            ),
        ),
        (
            "R005",
            0.60,
            RuleSeverity.MEDIUM,
            "HIGHER_IS_WORSE",
            (
                (0.60, RuleSeverity.MEDIUM),
                (1.00, RuleSeverity.HIGH),
            ),
        ),
        (
            "R006",
            0.30,
            RuleSeverity.MEDIUM,
            "HIGHER_IS_WORSE",
            (
                (0.30, RuleSeverity.MEDIUM),
                (0.50, RuleSeverity.HIGH),
            ),
        ),
        (
            "R007",
            2.0,
            RuleSeverity.MEDIUM,
            "LOWER_IS_WORSE",
            (
                (2.0, RuleSeverity.MEDIUM),
                (1.0, RuleSeverity.HIGH),
            ),
        ),
    ],
)
def test_rule_configuration_matches_expected_values(
    rule_configs,
    rule_id,
    expected_threshold,
    expected_severity,
    expected_direction,
    expected_thresholds,
):
    assert rule_id in rule_configs

    config = rule_configs[rule_id]

    assert config.threshold == expected_threshold
    assert config.severity == expected_severity
    assert config.severity_direction.value == expected_direction

    actual_thresholds = tuple(
        (
            threshold.threshold,
            threshold.severity,
        )
        for threshold in config.severity_thresholds
    )

    assert actual_thresholds == expected_thresholds


def test_rule_configuration_ids_are_unique(rule_configs):
    assert rule_configs
    assert len(rule_configs) == len(set(rule_configs))


def test_rule_configuration_contains_required_fields(rule_configs):
    for config in rule_configs.values():
        assert config.rule_id
        assert config.rule_name
        assert config.category
        assert config.severity is not None
        assert config.severity_direction is not None
        assert config.threshold is not None


def test_rule_configuration_thresholds_have_valid_severities(
    rule_configs,
):
    valid_severities = set(RuleSeverity)

    for config in rule_configs.values():
        for threshold in config.severity_thresholds:
            assert threshold.severity in valid_severities


def test_rule_configuration_thresholds_are_consistent_with_base_threshold(
    rule_configs,
):
    for config in rule_configs.values():
        if not config.severity_thresholds:
            continue

        thresholds = config.severity_thresholds

        assert thresholds[0].threshold == config.threshold
        assert thresholds[0].severity == config.severity