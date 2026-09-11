import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial.leverage.nfp_to_ebitda import NfpToEbitdaRule

R004_CONFIG = RuleConfig(
    rule_id="R004",
    rule_name="NFP / EBITDA leverage",
    category="leverage",
    threshold=5.0,
    severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(
            threshold=5.0,
            severity=RuleSeverity.MEDIUM,
        ),
        SeverityThreshold(
            threshold=7.0,
            severity=RuleSeverity.HIGH,
        ),
    ),
    input_field="nfp_to_ebitda",
    trigger_operator="GT",
)


def create_rule(
    config: RuleConfig = R004_CONFIG,
) -> NfpToEbitdaRule:
    return NfpToEbitdaRule(config)


def assert_result_matches_config(
    result,
    config: RuleConfig,
) -> None:
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold


@pytest.mark.parametrize(
    (
        "nfp_to_ebitda",
        "expected_status",
        "expected_severity",
    ),
    [
        (4.9, RuleStatus.NOT_TRIGGERED, RuleSeverity.LOW),
        (5.0, RuleStatus.NOT_TRIGGERED, RuleSeverity.MEDIUM),
        (5.1, RuleStatus.TRIGGERED, RuleSeverity.MEDIUM),
        (7.0, RuleStatus.TRIGGERED, RuleSeverity.HIGH),
        (8.5, RuleStatus.TRIGGERED, RuleSeverity.HIGH),
    ],
)
def test_nfp_to_ebitda_rule_evaluates_leverage_boundaries(
    nfp_to_ebitda,
    expected_status,
    expected_severity,
):
    position = CreditPosition(
        position_id="POS001",
        nfp_to_ebitda=nfp_to_ebitda,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == expected_status
    assert result.value == nfp_to_ebitda
    assert result.severity == expected_severity


def test_nfp_to_ebitda_rule_is_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS002",
        nfp_to_ebitda=None,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == R004_CONFIG.severity


def test_nfp_to_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="R004_CUSTOM_THRESHOLD",
        rule_name="Custom NFP / EBITDA leverage",
        category="leverage",
        threshold=6.0,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        input_field="nfp_to_ebitda",
        trigger_operator="GT",
    )

    position = CreditPosition(
        position_id="POS003",
        nfp_to_ebitda=5.5,
    )

    result = NfpToEbitdaRule(config).evaluate(position)

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 5.5


def test_nfp_to_ebitda_rule_uses_configured_input_field_and_operator():
    config = RuleConfig(
        rule_id="R004_CUSTOM_OPERATOR",
        rule_name="Configured NFP / EBITDA leverage",
        category="leverage",
        threshold=5.0,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        input_field="nfp_to_ebitda",
        trigger_operator="GTE",
    )

    position = CreditPosition(
        position_id="POS004",
        nfp_to_ebitda=5.0,
    )

    result = NfpToEbitdaRule(config).evaluate(position)

    assert result.value == 5.0
    assert result.status == RuleStatus.TRIGGERED
