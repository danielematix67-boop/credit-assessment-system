import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection


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


@pytest.mark.parametrize(
    "direction",
    list(SeverityDirection),
)
def test_rule_config_accepts_valid_severity_direction(
    rule_config_data,
    direction,
):
    data = {
        **rule_config_data,
        "severity_direction": direction,
    }

    config = RuleConfig(**data)

    assert config.severity_direction == direction


def test_rule_config_uses_default_severity_direction(
    rule_config,
):
    assert rule_config.severity_direction == SeverityDirection.HIGHER_IS_WORSE


def test_rule_config_uses_empty_severity_thresholds_by_default(
    rule_config,
):
    assert rule_config.severity_thresholds == ()


def test_rule_config_accepts_severity_thresholds(
    rule_config_data,
):
    config = RuleConfig(
        **rule_config_data,
        severity_thresholds=(),
    )

    assert config.severity_thresholds == ()


def test_rule_config_is_immutable(rule_config):
    with pytest.raises(AttributeError):
        rule_config.threshold = None


def test_rule_config_accepts_valid_configuration():
    config = RuleConfig(
        rule_id="R003",
        rule_name="EBITDA Margin",
        category="profitability",
        threshold=0.05,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    )

    assert config.rule_id == "R003"
    assert config.rule_name == "EBITDA Margin"
    assert config.category == "profitability"
    assert config.threshold == 0.05
    assert config.severity == RuleSeverity.MEDIUM
    assert config.severity_direction == SeverityDirection.HIGHER_IS_WORSE
    assert config.severity_thresholds == ()


def test_rule_config_accepts_direct_calculation_with_single_input():
    config = RuleConfig(
        rule_id="DIRECT",
        rule_name="Direct rule",
        category="test",
        threshold=1.0,
        severity=RuleSeverity.MEDIUM,
        input_field="metric",
        calculation="direct",
    )

    assert config.input_field == "metric"


def test_rule_config_accepts_ratio_with_two_inputs():
    config = RuleConfig(
        rule_id="RATIO",
        rule_name="Ratio rule",
        category="test",
        threshold=1.0,
        severity=RuleSeverity.MEDIUM,
        input_fields=("numerator", "denominator"),
        calculation="ratio",
    )

    assert config.input_fields == ("numerator", "denominator")


def test_rule_config_accepts_difference_with_two_inputs():
    config = RuleConfig(
        rule_id="DIFFERENCE",
        rule_name="Difference rule",
        category="test",
        threshold=1.0,
        severity=RuleSeverity.MEDIUM,
        input_fields=("left", "right"),
        calculation="difference",
    )

    assert config.input_fields == ("left", "right")


@pytest.mark.parametrize(
    ("calculation", "input_field", "input_fields"),
    [
        ("direct", "", ("a", "b")),
        ("ratio", "a", ()),
        ("ratio", "", ("a",)),
        ("difference", "", ("a",)),
        ("difference", "", ("a", "b", "c")),
    ],
)
def test_rule_config_rejects_inconsistent_input_count(
    calculation,
    input_field,
    input_fields,
):
    with pytest.raises(ValueError, match="requires exactly"):
        RuleConfig(
            rule_id="INVALID",
            rule_name="Invalid rule",
            category="test",
            threshold=1.0,
            severity=RuleSeverity.MEDIUM,
            input_field=input_field,
            input_fields=input_fields,
            calculation=calculation,
        )


def test_rule_config_rejects_both_input_field_and_input_fields():
    with pytest.raises(ValueError, match="cannot both be configured"):
        RuleConfig(
            rule_id="INVALID",
            rule_name="Invalid rule",
            category="test",
            threshold=1.0,
            severity=RuleSeverity.MEDIUM,
            input_field="metric",
            input_fields=("a", "b"),
            calculation="ratio",
        )
