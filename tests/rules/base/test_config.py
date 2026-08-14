import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        threshold=0.10,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.mark.parametrize(
    "field, expected",
    [
        ("rule_id", "TEST_RULE"),
        ("rule_name", "Test rule"),
        ("category", "test"),
        ("threshold", 0.10),
        ("severity", RuleSeverity.MEDIUM),
    ],
)
def test_rule_config_stores_configuration(
    rule_config,
    field,
    expected,
):
    assert getattr(rule_config, field) == expected


def test_rule_config_is_immutable(rule_config):
    with pytest.raises(AttributeError):
        rule_config.threshold = 0.20