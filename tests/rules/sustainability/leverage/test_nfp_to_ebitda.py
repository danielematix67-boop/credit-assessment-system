import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r004 import NfpToEbitdaRule

R004_CONFIG = RuleConfig(
    rule_id="R004",
    rule_name="nfp / EBITDA leverage",
    category="leverage",
    threshold=5.0,
    severity=RuleSeverity.HIGH,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(threshold=3.0, severity=RuleSeverity.LOW),
        SeverityThreshold(threshold=5.0, severity=RuleSeverity.MEDIUM),
        SeverityThreshold(threshold=7.0, severity=RuleSeverity.HIGH),
    ),
    input_field="nfp_to_ebitda",
)


def create_rule(config: RuleConfig = R004_CONFIG) -> NfpToEbitdaRule:
    return NfpToEbitdaRule(config)


def assert_result_matches_config(result, config: RuleConfig) -> None:
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold


def test_nfp_to_ebitda_rule_triggered():
    result = create_rule().evaluate(
        CreditPosition(position_id="POS001", nfp_to_ebitda=6.0)
    )
    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == 6.0
    assert result.severity == RuleSeverity.MEDIUM


def test_nfp_to_ebitda_rule_not_triggered():
    result = create_rule().evaluate(
        CreditPosition(position_id="POS002", nfp_to_ebitda=3.5)
    )
    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 3.5
    assert result.severity == RuleSeverity.LOW


def test_nfp_to_ebitda_rule_not_evaluable_when_none():
    result = create_rule().evaluate(
        CreditPosition(position_id="POS003", nfp_to_ebitda=None)
    )
    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == R004_CONFIG.severity


def test_nfp_to_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="R004_CUSTOM",
        rule_name="Custom nfp / EBITDA threshold",
        category=R004_CONFIG.category,
        threshold=7.0,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        input_field="nfp_to_ebitda",
    )
    result = create_rule(config).evaluate(
        CreditPosition(position_id="POS004", nfp_to_ebitda=6.0)
    )
    assert_result_matches_config(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 6.0
    assert result.severity == RuleSeverity.MEDIUM


@pytest.mark.parametrize(
    "nfp_to_ebitda, expected_severity, expected_status",
    [
        (3.0, RuleSeverity.LOW, RuleStatus.NOT_TRIGGERED),
        (4.0, RuleSeverity.LOW, RuleStatus.NOT_TRIGGERED),
        (5.0, RuleSeverity.MEDIUM, RuleStatus.NOT_TRIGGERED),
        (6.0, RuleSeverity.MEDIUM, RuleStatus.TRIGGERED),
        (7.0, RuleSeverity.HIGH, RuleStatus.TRIGGERED),
        (8.0, RuleSeverity.HIGH, RuleStatus.TRIGGERED),
    ],
)
def test_nfp_to_ebitda_rule_resolves_dynamic_severity(
    nfp_to_ebitda, expected_severity, expected_status
):
    result = create_rule().evaluate(
        CreditPosition(position_id="POS_DYNAMIC", nfp_to_ebitda=nfp_to_ebitda)
    )
    assert result.status == expected_status
    assert result.value == nfp_to_ebitda
    assert result.severity == expected_severity
