import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial.revenue.revenue_growth import RevenueGrowthRule


R001_CONFIG = RuleConfig(
    rule_id="R001",
    rule_name="Revenue deterioration",
    category="revenue",
    threshold=-0.10,
    severity=RuleSeverity.LOW,
    severity_direction=SeverityDirection.LOWER_IS_WORSE,
    severity_thresholds=(
        SeverityThreshold(
            threshold=-0.10,
            severity=RuleSeverity.MEDIUM,
        ),
        SeverityThreshold(
            threshold=-0.20,
            severity=RuleSeverity.HIGH,
        ),
    ),
)


def create_rule(
    config: RuleConfig = R001_CONFIG,
) -> RevenueGrowthRule:
    return RevenueGrowthRule(config)


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
        "revenue_growth",
        "expected_status",
        "expected_severity",
    ),
    [
        (
            0.05,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.LOW,
        ),
        (
            -0.05,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.LOW,
        ),
        (
            -0.10,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.MEDIUM,
        ),
        (
            -0.15,
            RuleStatus.TRIGGERED,
            RuleSeverity.MEDIUM,
        ),
        (
            -0.20,
            RuleStatus.TRIGGERED,
            RuleSeverity.HIGH,
        ),
        (
            -0.25,
            RuleStatus.TRIGGERED,
            RuleSeverity.HIGH,
        ),
    ],
)
def test_revenue_growth_rule_evaluates_dynamic_severity(
    revenue_growth,
    expected_status,
    expected_severity,
):
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=revenue_growth,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R001_CONFIG)
    assert result.status == expected_status
    assert result.value == revenue_growth
    assert result.severity == expected_severity


def test_revenue_growth_rule_is_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=None,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R001_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == R001_CONFIG.severity


def test_revenue_growth_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id=f"{R001_CONFIG.rule_id}_CUSTOM",
        rule_name="Custom revenue deterioration",
        category=R001_CONFIG.category,
        threshold=-0.20,
        severity=RuleSeverity.LOW,
        severity_direction=SeverityDirection.LOWER_IS_WORSE,
        severity_thresholds=(
            SeverityThreshold(
                threshold=-0.20,
                severity=RuleSeverity.MEDIUM,
            ),
            SeverityThreshold(
                threshold=-0.30,
                severity=RuleSeverity.HIGH,
            ),
        ),
    )

    revenue_growth = -0.15

    position = CreditPosition(
        position_id="POS003",
        revenue_growth=revenue_growth,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule(config).evaluate(position)

    assert_result_matches_config(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == revenue_growth
    assert result.severity == RuleSeverity.LOW