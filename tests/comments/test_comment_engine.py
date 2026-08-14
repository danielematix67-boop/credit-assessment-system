import pytest
from dataclasses import replace

from src.comments.comment_engine import CommentEngine
from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.financial.revenue.revenue_growth import RevenueGrowthRule
from src.rules.financial.profitability.negative_ebitda import (
    NegativeEbitdaRule,
)
from src.rules.financial.margins.ebitda_margin import EbitdaMarginRule
from src.rules.result import RuleResult
from src.rules.sustainability.leverage.pfn_to_ebitda import (
    PfnToEbitdaRule,
)
from src.rules.financial.profitability.financial_expenses_to_ebitda import (
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


@pytest.mark.parametrize(
    "rule_class, rule_id, rule_name, category, threshold, severity, position_changes",
    [
        (
            RevenueGrowthRule,
            "R001",
            "Revenue growth deterioration",
            "revenue",
            -0.10,
            RuleSeverity.MEDIUM,
            {"revenue_growth": -0.15},
        ),
        (
            NegativeEbitdaRule,
            "R002",
            "Negative EBITDA",
            "profitability",
            0.0,
            RuleSeverity.HIGH,
            {"ebitda": -50000},
        ),
        (
            EbitdaMarginRule,
            "R003",
            "EBITDA margin deterioration",
            "profitability",
            0.0,
            RuleSeverity.MEDIUM,
            {"ebitda_margin": -0.05},
        ),
        (
            PfnToEbitdaRule,
            "R004",
            "PFN / EBITDA leverage",
            "leverage",
            5.0,
            RuleSeverity.HIGH,
            {"pfn_to_ebitda": 6.0},
        ),
        (
            FinancialExpensesToEbitdaRule,
            "R005",
            "Interest expense to EBITDA",
            "profitability",
            0.60,
            RuleSeverity.MEDIUM,
            {"interest_expense": 200000},
        ),
    ],
)
def test_comment_generated_for_triggered_rule(
    base_position,
    rule_class,
    rule_id,
    rule_name,
    category,
    threshold,
    severity,
    position_changes,
):
    position = replace(base_position, **position_changes)

    config = RuleConfig(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        threshold=threshold,
        severity=severity,
    )

    rule = rule_class(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert result.status == RuleStatus.TRIGGERED

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text


def test_no_comment_generated_when_rule_is_not_triggered(base_position):
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(base_position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert result.status != RuleStatus.TRIGGERED
    assert comment is None


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
        severity=RuleSeverity.MEDIUM,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert comment is None


def test_no_comment_generated_when_rule_has_no_template():
    result = RuleResult(
        rule_id="R999",
        rule_name="Custom rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=10.0,
        threshold=5.0,
        severity=RuleSeverity.MEDIUM,
    )

    engine = CommentEngine()

    comment = engine.generate(result)

    assert comment is None


def test_comment_engine_renders_rule_value():
    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.20,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    engine = CommentEngine()

    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text

    # The deterministic result retains the threshold.
    assert result.threshold == -0.10

    # The comment should contain the evaluated value,
    # while its exact wording remains implementation-independent.
    assert "-20.0%" in comment.text


def test_comment_engine_does_not_modify_rule_result():
    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    original_result = result

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None

    assert result is original_result
    assert result.value == -0.15
    assert result.threshold == -0.10
    assert result.status == RuleStatus.TRIGGERED