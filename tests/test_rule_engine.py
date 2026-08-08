from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.profitability_rules import NegativeEbitdaRule
from src.rules.revenue_rules import RevenueGrowthRule


def test_rule_engine_evaluates_all_rules():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
    )

    rules = [
        RevenueGrowthRule(),
        NegativeEbitdaRule(),
    ]

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert len(results) == 2

    assert results[0].rule_id == "R001"
    assert results[0].triggered is True

    assert results[1].rule_id == "R002"
    assert results[1].triggered is True