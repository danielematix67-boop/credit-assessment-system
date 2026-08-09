from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule


def test_rule_engine_evaluates_all_rules():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6,
        interest_expense=40000,
    )

    rules = [
        RevenueGrowthRule(),
        NegativeEbitdaRule(),
        EbitdaMarginRule(),
        PfnToEbitdaRule(),
    ]

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert len(results) == 4

    assert results[0].rule_id == "R001"
    assert results[0].status == RuleStatus.TRIGGERED

    assert results[1].rule_id == "R002"
    assert results[1].status == RuleStatus.TRIGGERED

    assert results[2].rule_id == "R003"
    assert results[2].status == RuleStatus.TRIGGERED

    assert results[3].rule_id == "R004"
    assert results[3].status == RuleStatus.TRIGGERED


def test_rule_engine_preserves_rule_order():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6,
        interest_expense=40000,
    )

    rules = [
        PfnToEbitdaRule(),
        RevenueGrowthRule(),
        EbitdaMarginRule(),
        NegativeEbitdaRule(),
    ]

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert [result.rule_id for result in results] == [
        "R004",
        "R001",
        "R003",
        "R002",
    ]


def test_rule_engine_with_no_rules():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    engine = RuleEngine([])

    results = engine.evaluate(position)

    assert results == []
