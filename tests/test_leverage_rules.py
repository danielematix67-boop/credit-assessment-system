from src.models.position import CreditPosition
from src.rules.leverage_rules import PfnToEbitdaRule


def test_pfn_to_ebitda_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=6.0,
    )

    rule = PfnToEbitdaRule()
    result = rule.evaluate(position)

    assert result.rule_id == "R004"
    assert result.triggered is True
    assert result.value == 6.0
    assert result.threshold == 5.0


def test_pfn_to_ebitda_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
    )

    rule = PfnToEbitdaRule()
    result = rule.evaluate(position)

    assert result.rule_id == "R004"
    assert result.triggered is False
    assert result.value == 3.5
    assert result.threshold == 5.0