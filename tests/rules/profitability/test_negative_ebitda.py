from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule


R002_CONFIG = RuleConfig(
    rule_id="R002",
    rule_name="Negative EBITDA",
    category="profitability",
    threshold=0.0,
)


def test_negative_ebitda_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = NegativeEbitdaRule(R002_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R002"
    assert result.rule_name == "Negative EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == -50000
    assert result.threshold == 0.0


def test_negative_ebitda_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = NegativeEbitdaRule(R002_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R002"
    assert result.rule_name == "Negative EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 250000
    assert result.threshold == 0.0


def test_negative_ebitda_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=None,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = NegativeEbitdaRule(R002_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R002"
    assert result.rule_name == "Negative EBITDA"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == 0.0


def test_negative_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="R002_CUSTOM",
        rule_name="Custom EBITDA threshold",
        category="profitability",
        threshold=-100000.0,
    )

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=-50000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = NegativeEbitdaRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R002_CUSTOM"
    assert result.rule_name == "Custom EBITDA threshold"
    assert result.category == "profitability"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == -50000
    assert result.threshold == -100000.0
