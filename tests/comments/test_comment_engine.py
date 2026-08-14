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
        severity=RuleSeverity.MEDIUM,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R001"
    assert comment.text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0%."
    )

    # The threshold remains part of the deterministic
    # RuleResult but is not exposed in the comment.
    assert result.threshold == -0.10
    assert "threshold" not in comment.text.lower()


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
        severity=RuleSeverity.HIGH,
    )

    rule = NegativeEbitdaRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R002"
    assert comment.text == (
        "Negative EBITDA detected. "
        "EBITDA: €-50,000."
    )

    assert result.threshold == 0.0
    assert "threshold" not in comment.text.lower()


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
        severity=RuleSeverity.MEDIUM,
    )

    rule = EbitdaMarginRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R003"
    assert comment.text == (
        "EBITDA margin is below the acceptable threshold. "
        "EBITDA margin: -5.0%."
    )

    assert result.threshold == 0.0
    assert "threshold" in comment.text.lower()


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
        severity=RuleSeverity.HIGH,
    )

    rule = PfnToEbitdaRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R004"
    assert comment.text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x."
    )

    assert result.threshold == 5.0
    assert "threshold" in comment.text.lower()


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
        severity=RuleSeverity.MEDIUM,
    )

    rule = FinancialExpensesToEbitdaRule(config)
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R005"
    assert comment.text == (
        "Interest expense to EBITDA is above the acceptable threshold. "
        "Ratio: 80.0%."
    )

    assert result.threshold == 0.60
    assert "threshold" in comment.text.lower()


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


def test_comment_engine_formats_value_without_threshold():
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
    assert comment.text == (
        "Revenue deterioration detected. "
        "Revenue growth: -20.0%."
    )

    # The threshold remains available to the deterministic
    # layer but is not exposed in the generated comment.
    assert result.threshold == -0.10
    assert "threshold" not in comment.text.lower()


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