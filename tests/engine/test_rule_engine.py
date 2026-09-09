from unittest.mock import MagicMock

import pytest

from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.registry import get_default_rules
from src.rules.result import RuleResult

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def position():
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40000,
    )


@pytest.fixture
def rules_position():
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        nfp_to_ebitda=6.0,
        interest_expense=40000,
    )


@pytest.fixture
def rule_result():
    return RuleResult(
        rule_id="RULE_ID",
        rule_name="Rule name",
        category="category",
        status=RuleStatus.TRIGGERED,
        value=10.0,
        threshold=5.0,
        severity=RuleSeverity.HIGH,
    )


# ============================================================
# Single rule delegation
# ============================================================


def test_rule_engine_returns_result_produced_by_rule(
    position,
    rule_result,
):
    rule = MagicMock()
    rule.evaluate.return_value = rule_result

    engine = RuleEngine([rule])

    results = engine.evaluate(position)

    assert results == [rule_result]
    assert results[0] is rule_result

    rule.evaluate.assert_called_once_with(position)


# ============================================================
# Multiple rules
# ============================================================


def test_rule_engine_evaluates_every_configured_rule(
    position,
    rule_result,
):
    rules = []

    for index in range(3):
        rule = MagicMock()
        rule.evaluate.return_value = rule_result
        rules.append(rule)

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert len(results) == len(rules)

    for rule in rules:
        rule.evaluate.assert_called_once_with(position)


def test_rule_engine_returns_one_result_per_rule(
    position,
):
    rules = []

    results_by_rule = {}

    for index in range(3):
        rule = MagicMock()

        result = MagicMock()
        rule.evaluate.return_value = result

        rules.append(rule)
        results_by_rule[id(rule)] = result

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert len(results) == len(rules)

    assert all(result in results for result in results_by_rule.values())


# ============================================================
# Order preservation
# ============================================================


def test_rule_engine_preserves_rule_evaluation_order(
    position,
):
    rule_ids = ["FIRST", "SECOND", "THIRD"]

    rules = []

    for rule_id in rule_ids:
        rule = MagicMock()
        rule.evaluate.return_value = RuleResult(
            rule_id=rule_id,
            rule_name="Rule",
            category="category",
            status=RuleStatus.TRIGGERED,
            value=1.0,
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
        )

        rules.append(rule)

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert [result.rule_id for result in results] == [
        rule.evaluate.return_value.rule_id for rule in rules
    ]


# ============================================================
# Empty configuration
# ============================================================


def test_rule_engine_returns_empty_result_for_no_rules(
    position,
):
    engine = RuleEngine([])

    results = engine.evaluate(position)

    assert results == []


# ============================================================
# Default rule configuration
# ============================================================


def test_rule_engine_evaluates_all_default_rules(
    rules_position,
):
    rules = get_default_rules()

    engine = RuleEngine(rules)

    results = engine.evaluate(rules_position)

    assert results

    assert len(results) == len(rules)

    result_rule_ids = {result.rule_id for result in results}

    configured_rule_ids = {rule.config.rule_id for rule in rules}

    assert result_rule_ids == configured_rule_ids


# ============================================================
# Status preservation
# ============================================================


@pytest.mark.parametrize(
    "status",
    list(RuleStatus),
)
def test_rule_engine_preserves_rule_result_status(
    position,
    status,
):
    rule = MagicMock()

    result = MagicMock()
    result.status = status

    rule.evaluate.return_value = result

    engine = RuleEngine([rule])

    results = engine.evaluate(position)

    assert results[0] is result
    assert results[0].status == status


# ============================================================
# Non-evaluable results
# ============================================================


def test_rule_engine_preserves_not_evaluable_results(
    position,
):
    rule = MagicMock()

    result = RuleResult(
        rule_id="RULE_ID",
        rule_name="Rule name",
        category="category",
        status=RuleStatus.NOT_EVALUABLE,
        value=None,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )

    rule.evaluate.return_value = result

    engine = RuleEngine([rule])

    results = engine.evaluate(position)

    assert results == [result]
    assert results[0] is result
    assert results[0].status == RuleStatus.NOT_EVALUABLE
    assert results[0].value is None


# ============================================================
# Input propagation
# ============================================================


def test_rule_engine_passes_same_position_to_every_rule(
    position,
):
    rules = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]

    for rule in rules:
        rule.evaluate.return_value = MagicMock()

    engine = RuleEngine(rules)

    engine.evaluate(position)

    for rule in rules:
        rule.evaluate.assert_called_once_with(position)
