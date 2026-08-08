from src.models.position import CreditPosition
from src.rules.profitability_rules import NegativeEbitdaRule


def test_negative_ebitda_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
    )

    rule = NegativeEbitdaRule()
    result = rule.evaluate(position)

    assert result.rule_id == "R002"
    assert result.category == "profitability"
    assert result.triggered is True
    assert result.value == -50000
    assert result.threshold == 0


def test_negative_ebitda_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
    )

    rule = NegativeEbitdaRule()
    result = rule.evaluate(position)

    assert result.rule_id == "R002"
    assert result.category == "profitability"
    assert result.triggered is False
    assert result.value == 250000
    assert result.threshold == 0