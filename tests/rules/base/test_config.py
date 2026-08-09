import pytest

from src.rules.base.config import RuleConfig


def test_rule_config_stores_configuration():
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
    )

    assert config.rule_id == "R001"
    assert config.rule_name == "Revenue growth deterioration"
    assert config.category == "revenue"
    assert config.threshold == -0.10


def test_rule_config_is_immutable():
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
    )

    with pytest.raises(AttributeError):
        config.threshold = -0.20