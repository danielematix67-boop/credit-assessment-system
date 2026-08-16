import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


@pytest.fixture
def rule_config_data():
    return {
        "rule_id": "TEST_RULE",
        "rule_name": "Test rule",
        "category": "test",
        "threshold": 0.10,
        "severity": RuleSeverity.MEDIUM,
    }


@pytest.fixture
def rule_config(rule_config_data):
    return RuleConfig(**rule_config_data)


def test_rule_config_preserves_provided_data(
    rule_config,
    rule_config_data,
):
    for field_name, expected_value in rule_config_data.items():
        assert getattr(rule_config, field_name) == expected_value


@pytest.mark.parametrize(
    "severity",
    list(RuleSeverity),
)
def test_rule_config_accepts_valid_severity(
    rule_config_data,
    severity,
):
    data = {
        **rule_config_data,
        "severity": severity,
    }

    config = RuleConfig(**data)

    assert config.severity == severity


def test_rule_config_is_immutable(rule_config):
    with pytest.raises(AttributeError):
        rule_config.threshold = None