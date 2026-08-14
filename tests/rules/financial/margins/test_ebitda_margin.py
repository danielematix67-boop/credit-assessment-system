from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.financial.margins.ebitda_margin import EbitdaMarginRule


R003_CONFIG = RuleConfig(
    rule_id="R003",
    rule_name="EBITDA margin deterioration",
    category="profitability",
    threshold=0.0,
    severity=RuleSeverity.MEDIUM,
)


def create_rule(
    config: RuleConfig = R003_CONFIG,
) -> EbitdaMarginRule:
    return EbitdaMarginRule(config)


def assert_result_matches_config(
    result,
    config: RuleConfig,
) -> None:
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold
    assert result.severity == config.severity


def test_ebitda_margin_rule_triggered():
    ebitda_margin = -0.05

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50_000,
        profit_loss=-50_000,
        ebitda_margin=ebitda_margin,
        pfn_to_ebitda=6.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R003_CONFIG)
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == ebitda_margin


def test_ebitda_margin_rule_not_triggered():
    ebitda_margin = 0.12

    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=ebitda_margin,
        pfn_to_ebitda=2.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R003_CONFIG)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == ebitda_margin


def test_ebitda_margin_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=None,
        pfn_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R003_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_ebitda_margin_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id=f"{R003_CONFIG.rule_id}_CUSTOM",
        rule_name="Custom EBITDA margin threshold",
        category=R003_CONFIG.category,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    ebitda_margin = -0.05

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=-25_000,
        profit_loss=-5_000,
        ebitda_margin=ebitda_margin,
        pfn_to_ebitda=3.5,
        interest_expense=40_000,
    )

    result = create_rule(config).evaluate(position)

    assert_result_matches_config(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == ebitda_margin