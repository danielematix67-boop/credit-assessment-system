from unittest.mock import MagicMock

from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.registry import get_default_rules
from src.rules.result import RuleResult


def test_rule_engine_returns_rule_results_produced_by_rules():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = MagicMock()

    expected_result = RuleResult(
        rule_id="TEST_1",
        rule_name="Test rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=10.0,
        threshold=5.0,
        severity=RuleSeverity.HIGH,
    )

    rule.evaluate.return_value = expected_result

    engine = RuleEngine([rule])

    results = engine.evaluate(position)

    assert results == [expected_result]
    assert results[0] is expected_result
    rule.evaluate.assert_called_once_with(position)



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

    rules = get_default_rules()

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    # One result must be produced for every configured rule.
    assert len(results) == len(rules)

    # Every configured rule must produce exactly one result.
    assert {
        result.rule_id
        for result in results
    } == {
        rule.config.rule_id
        for rule in rules
    }


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

    rule_1 = MagicMock()
    rule_1.config.rule_id = "TEST_1"
    rule_1.evaluate.return_value.rule_id = "TEST_1"

    rule_2 = MagicMock()
    rule_2.config.rule_id = "TEST_2"
    rule_2.evaluate.return_value.rule_id = "TEST_2"

    rule_3 = MagicMock()
    rule_3.config.rule_id = "TEST_3"
    rule_3.evaluate.return_value.rule_id = "TEST_3"

    rules = [rule_1, rule_2, rule_3]

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert [
        result.rule_id
        for result in results
    ] == [
        "TEST_1",
        "TEST_2",
        "TEST_3",
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


def test_rule_engine_preserves_not_evaluable_status():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rules = get_default_rules()

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    revenue_growth_result = next(
        result
        for result in results
        if result.rule_id == "R001"
    )

    assert revenue_growth_result.status == RuleStatus.NOT_EVALUABLE
    assert revenue_growth_result.value is None
    assert revenue_growth_result.threshold == -0.10

    inventory_contribution_result = next(
        result
        for result in results
        if result.rule_id == "R006"
    )

    assert inventory_contribution_result.status == RuleStatus.NOT_EVALUABLE
    assert inventory_contribution_result.value is None

