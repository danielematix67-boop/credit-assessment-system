from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.profitability.ebitda_margin import EbitdaMarginRule


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

    config = RuleConfig(
        rule_id="R003",
        rule_name="EBITDA margin deterioration",
        category="profitability",
        threshold=0.0,
    )

    rule = EbitdaMarginRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R003"
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

    config = RuleConfig(
        rule_id="R003",
        rule_name="EBITDA margin deterioration",
        category="profitability",
        threshold=0.0,
    )

    rule = EbitdaMarginRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R003"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.12
    assert result.threshold == 0.0


def test_ebitda_margin_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=None,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    config = RuleConfig(
        rule_id="R003",
        rule_name="EBITDA margin deterioration",
        category="profitability",
        threshold=0.0,
    )

    rule = EbitdaMarginRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R003"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.0
