from src.models.position import CreditPosition
from src.rules.revenue_rules import RevenueGrowthRule


def test_revenue_growth_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=250000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=40000
    )

    rule = RevenueGrowthRule()
    result = rule.evaluate(position)

    assert result.rule_id == "R001"
    assert result.triggered is True
    assert result.value == -0.15
    assert result.threshold == -0.10
    assert result.category == "revenue"

def test_revenue_growth_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=40000
    )

    rule = RevenueGrowthRule()
    result = rule.evaluate(position)

    assert result.rule_id == "R001"
    assert result.triggered is False
    assert result.value == 0.05
    assert result.threshold == -0.10
    assert result.category == "revenue"

def test_revenue_growth_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = RevenueGrowthRule()

    result = rule.evaluate(position)

    assert result.rule_id == "R001"
    assert result.triggered is False
    assert result.value is None
    assert result.threshold == -0.10
    assert result.status == "NOT_EVALUABLE"

