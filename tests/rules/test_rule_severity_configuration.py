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
        for config in loader.load(
            RULES_CONFIG_PATH
        )
    }


def test_r001_revenue_growth_severity(rule_configs):
    config = rule_configs["R001"]

    assert config.threshold == -0.10
    assert config.severity == RuleSeverity.MEDIUM

    assert config.severity_direction.value == "LOWER_IS_WORSE"

    assert config.severity_thresholds[0].threshold == -0.10
    assert (
        config.severity_thresholds[0].severity
        == RuleSeverity.MEDIUM
    )

    assert config.severity_thresholds[1].threshold == -0.30
    assert (
        config.severity_thresholds[1].severity
        == RuleSeverity.HIGH
    )


def test_r002_negative_ebitda_configuration(rule_configs):
    config = rule_configs["R002"]

    assert config.threshold == 0.0
    assert config.severity == RuleSeverity.HIGH
    assert (
        config.severity_direction.value
        == "LOWER_IS_WORSE"
    )

    assert config.severity_thresholds == ()


def test_r003_ebitda_margin_severity(rule_configs):
    config = rule_configs["R003"]

    assert config.threshold == 0.0
    assert config.severity == RuleSeverity.MEDIUM

    assert (
        config.severity_direction.value
        == "LOWER_IS_WORSE"
    )

    assert config.severity_thresholds[0].threshold == 0.0
    assert (
        config.severity_thresholds[0].severity
        == RuleSeverity.MEDIUM
    )

    assert config.severity_thresholds[1].threshold == -0.10
    assert (
        config.severity_thresholds[1].severity
        == RuleSeverity.HIGH
    )


def test_r004_leverage_severity(rule_configs):
    config = rule_configs["R004"]

    assert config.threshold == 5.0
    assert config.severity == RuleSeverity.MEDIUM

    assert (
        config.severity_direction.value
        == "HIGHER_IS_WORSE"
    )

    assert config.severity_thresholds[0].threshold == 5.0
    assert (
        config.severity_thresholds[0].severity
        == RuleSeverity.MEDIUM
    )

    assert config.severity_thresholds[1].threshold == 7.0
    assert (
        config.severity_thresholds[1].severity
        == RuleSeverity.HIGH
    )


def test_r005_interest_expense_to_ebitda(rule_configs):
    config = rule_configs["R005"]

    assert config.threshold == 0.60
    assert config.severity == RuleSeverity.MEDIUM

    assert (
        config.severity_direction.value
        == "HIGHER_IS_WORSE"
    )

    assert config.severity_thresholds[0].threshold == 0.60
    assert (
        config.severity_thresholds[0].severity
        == RuleSeverity.MEDIUM
    )

    assert config.severity_thresholds[1].threshold == 1.00
    assert (
        config.severity_thresholds[1].severity
        == RuleSeverity.HIGH
    )


def test_r006_inventory_supported_ebitda(rule_configs):
    config = rule_configs["R006"]

    assert config.threshold == 0.30
    assert config.severity == RuleSeverity.MEDIUM

    assert (
        config.severity_direction.value
        == "HIGHER_IS_WORSE"
    )

    assert config.severity_thresholds[0].threshold == 0.30
    assert (
        config.severity_thresholds[0].severity
        == RuleSeverity.MEDIUM
    )

    assert config.severity_thresholds[1].threshold == 0.50
    assert (
        config.severity_thresholds[1].severity
        == RuleSeverity.HIGH
    )


def test_r007_interest_coverage(rule_configs):
    config = rule_configs["R007"]

    assert config.threshold == 2.0
    assert config.severity == RuleSeverity.MEDIUM

    assert (
        config.severity_direction.value
        == "LOWER_IS_WORSE"
    )

    assert config.severity_thresholds[0].threshold == 2.0
    assert (
        config.severity_thresholds[0].severity
        == RuleSeverity.MEDIUM
    )

    assert config.severity_thresholds[1].threshold == 1.0
    assert (
        config.severity_thresholds[1].severity
        == RuleSeverity.HIGH
    )