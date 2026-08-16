import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.sustainability.leverage.pfn_to_ebitda import (
    PfnToEbitdaRule,
)


R004_CONFIG = RuleConfig(
    rule_id="R004",
    rule_name="PFN / EBITDA leverage",
    category="leverage",
    threshold=5.0,
    severity=RuleSeverity.HIGH,
    severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(
            threshold=3.0,
            severity=RuleSeverity.LOW,
        ),
        SeverityThreshold(
            threshold=5.0,
            severity=RuleSeverity.MEDIUM,
        ),
        SeverityThreshold(
            threshold=7.0,
            severity=RuleSeverity.HIGH,
        ),
    ),
)


def create_rule(
    config: RuleConfig = R004_CONFIG,
) -> PfnToEbitdaRule:
    return PfnToEbitdaRule(config)


def assert_result_matches_config(
    result,
    config: RuleConfig,
) -> None:
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold


def test_pfn_to_ebitda_rule_triggered():
    pfn_to_ebitda = 6.0

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == pfn_to_ebitda
    assert result.severity == RuleSeverity.MEDIUM


def test_pfn_to_ebitda_rule_not_triggered():
    pfn_to_ebitda = 3.5

    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == pfn_to_ebitda
    assert result.severity == RuleSeverity.LOW


def test_pfn_to_ebitda_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=None,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == R004_CONFIG.severity


def test_pfn_to_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id=f"{R004_CONFIG.rule_id}_CUSTOM",
        rule_name="Custom PFN / EBITDA threshold",
        category=R004_CONFIG.category,
        threshold=7.0,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.HIGHER_IS_WORSE,
    )

    pfn_to_ebitda = 6.0

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule(config).evaluate(position)

    assert_result_matches_config(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == pfn_to_ebitda
    assert result.severity == RuleSeverity.MEDIUM


@pytest.mark.parametrize(
    "pfn_to_ebitda, expected_severity, expected_status",
    [
        (3.0, RuleSeverity.LOW, RuleStatus.NOT_TRIGGERED),
        (4.0, RuleSeverity.LOW, RuleStatus.NOT_TRIGGERED),
        (5.0, RuleSeverity.MEDIUM, RuleStatus.NOT_TRIGGERED),
        (6.0, RuleSeverity.MEDIUM, RuleStatus.TRIGGERED),
        (7.0, RuleSeverity.HIGH, RuleStatus.TRIGGERED),
        (8.0, RuleSeverity.HIGH, RuleStatus.TRIGGERED),
    ],
)
def test_pfn_to_ebitda_rule_resolves_dynamic_severity(
    pfn_to_ebitda,
    expected_severity,
    expected_status,
):
    position = CreditPosition(
        position_id="POS_DYNAMIC",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert result.status == expected_status
    assert result.value == pfn_to_ebitda
    assert result.severity == expected_severity