import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


def test_rule_config_stores_configuration():
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    assert config.rule_id == "R001"
    assert config.rule_name == "Revenue growth deterioration"
    assert config.category == "revenue"
    assert config.threshold == -0.10
    assert config.severity == RuleSeverity.MEDIUM


def test_rule_config_is_immutable():
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    with pytest.raises(AttributeError):
        config.threshold = -0.20
