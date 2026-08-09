from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.profitability.ebitda_margin import EbitdaMarginRule


R003_CONFIG = RuleConfig(
    rule_id="R003",
    rule_name="EBITDA margin deterioration",
    category="profitability",
    threshold=0.0,
)


def test_ebitda_margin_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.5,
        interest_expense=40000,
    )

    rule = EbitdaMarginRule(R003_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R003"
    assert result.rule_name == "EBITDA margin deterioration"
    assert result.category == "profitability"
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == -0.05
    assert result.threshold == 0.0


def test_ebitda_margin_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.12,
        pfn_to_ebitda=2.5,
        interest_expense=40000,
    )

    rule = EbitdaMarginRule(R003_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R003"
    assert result.rule_name == "EBITDA margin deterioration"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.12
    assert result.threshold == 0.0


def test_ebitda_margin_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=None,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = EbitdaMarginRule(R003_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R003"
    assert result.rule_name == "EBITDA margin deterioration"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.0


def test_ebitda_margin_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="R003_CUSTOM",
        rule_name="Custom EBITDA margin threshold",
        category="profitability",
        threshold=-0.10,
    )

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=-25000,
        profit_loss=-5000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = EbitdaMarginRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R003_CUSTOM"
    assert result.rule_name == "Custom EBITDA margin threshold"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == -0.05
    assert result.threshold == -0.10
