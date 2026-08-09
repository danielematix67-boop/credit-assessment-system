import pytest
from dataclasses import replace

from src.comments.comment_engine import CommentEngine
from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)


@pytest.fixture
def base_position():
    return CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )


def test_comment_generated_when_rule_is_triggered(base_position):
    position = replace(
        base_position,
        revenue_growth=-0.15,
    )

    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R001"
    assert comment.text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0% "
        "(threshold: -10.0%)."
    )


def test_no_comment_generated_when_rule_is_not_triggered(base_position):
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(base_position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is None


def test_negative_ebitda_comment_generated(base_position):
    position = replace(
        base_position,
        ebitda=-50000,
    )

    config = RuleConfig(
        rule_id="R002",
        rule_name="Negative EBITDA",
        category="profitability",
        threshold=0.0,
    )

    rule = NegativeEbitdaRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R002"
    assert comment.text == (
        "Negative EBITDA detected. "
        "EBITDA: €-50,000 "
        "(threshold: €0)."
    )


def test_ebitda_margin_comment_generated(base_position):
    position = replace(
        base_position,
        ebitda_margin=-0.05,
    )

    config = RuleConfig(
        rule_id="R003",
        rule_name="EBITDA margin deterioration",
        category="profitability",
        threshold=0.0,
    )

    rule = EbitdaMarginRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R003"
    assert comment.text == (
        "EBITDA margin is below the acceptable threshold. "
        "EBITDA margin: -5.0% "
        "(threshold: 0.0%)."
    )


def test_pfn_to_ebitda_comment_generated(base_position):
    position = replace(
        base_position,
        pfn_to_ebitda=6.0,
    )

    config = RuleConfig(
        rule_id="R004",
        rule_name="PFN / EBITDA leverage",
        category="leverage",
        threshold=5.0,
    )

    rule = PfnToEbitdaRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R004"
    assert comment.text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x "
        "(threshold: 5.0x)."
    )


def test_interest_expense_to_ebitda_comment_generated(base_position):
    position = replace(
        base_position,
        interest_expense=200000,
    )

    config = RuleConfig(
        rule_id="R005",
        rule_name="Interest expense to EBITDA",
        category="profitability",
        threshold=0.60,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R005"
    assert comment.text == (
        "Interest expense to EBITDA is above the acceptable threshold. "
        "Ratio: 80.0% "
        "(threshold: 60.0%)."
    )

def test_no_comment_generated_when_rule_is_not_evaluable(base_position):
    position = replace(
        base_position,
        revenue_growth=None,
    )

    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert comment is None

