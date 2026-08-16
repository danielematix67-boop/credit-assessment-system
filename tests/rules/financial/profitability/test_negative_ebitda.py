from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.financial.profitability.negative_ebitda import (
    NegativeEbitdaRule,
)


R002_CONFIG = RuleConfig(
    rule_id="R002",
    rule_name="Negative EBITDA",
    category="profitability",
    threshold=0.0,
    severity=RuleSeverity.HIGH,
    severity_direction=SeverityDirection.LOWER_IS_WORSE,
)


def create_rule(
    config: RuleConfig = R002_CONFIG,
) -> NegativeEbitdaRule:
    return NegativeEbitdaRule(config)


def assert_result_matches_config(
    result,
    config: RuleConfig,
) -> None:
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold
    assert result.severity == config.severity


def test_negative_ebitda_rule_triggered():
    ebitda = -50_000

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=ebitda,
        profit_loss=-50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R002_CONFIG)
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == ebitda


def test_negative_ebitda_rule_not_triggered():
    ebitda = 250_000

    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=ebitda,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R002_CONFIG)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == ebitda


def test_negative_ebitda_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=None,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R002_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_negative_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id=f"{R002_CONFIG.rule_id}_CUSTOM",
        rule_name="Custom EBITDA threshold",
        category=R002_CONFIG.category,
        threshold=-100_000.0,
        severity=RuleSeverity.MEDIUM,
        severity_direction=SeverityDirection.LOWER_IS_WORSE,
    )

    ebitda = -50_000

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=ebitda,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule(config).evaluate(position)

    assert_result_matches_config(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == ebitda