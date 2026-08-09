from src.models.assessment_status import AssessmentStatus
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import (
    AssessmentStatusCalculator,
)


def test_returns_normal_when_no_rules_are_triggered():
    results = [
        RuleResult(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            status=RuleStatus.NOT_TRIGGERED,
            value=0.05,
            threshold=-0.10,
        ),
        RuleResult(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            status=RuleStatus.NOT_TRIGGERED,
            value=250000,
            threshold=0.0,
        ),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.NORMAL


def test_returns_attention_when_at_least_one_rule_is_triggered():
    results = [
        RuleResult(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            status=RuleStatus.TRIGGERED,
            value=-0.15,
            threshold=-0.10,
        ),
        RuleResult(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            status=RuleStatus.NOT_TRIGGERED,
            value=250000,
            threshold=0.0,
        ),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.ATTENTION


def test_returns_normal_when_rules_are_not_evaluable():
    results = [
        RuleResult(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            status=RuleStatus.NOT_EVALUABLE,
            value=None,
            threshold=-0.10,
        ),
        RuleResult(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            status=RuleStatus.NOT_EVALUABLE,
            value=None,
            threshold=0.0,
        ),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.NORMAL


def test_returns_attention_when_triggered_and_not_evaluable_rules_are_present():
    results = [
        RuleResult(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            status=RuleStatus.TRIGGERED,
            value=-0.15,
            threshold=-0.10,
        ),
        RuleResult(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            status=RuleStatus.NOT_EVALUABLE,
            value=None,
            threshold=0.0,
        ),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.ATTENTION


def test_returns_normal_when_results_are_empty():
    calculator = AssessmentStatusCalculator()

    status = calculator.calculate([])

    assert status == AssessmentStatus.NORMAL

def test_returns_critical_when_multiple_rules_are_triggered():
    results = [
        RuleResult(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            status=RuleStatus.TRIGGERED,
            value=-0.15,
            threshold=-0.10,
        ),
        RuleResult(
            rule_id="R003",
            rule_name="EBITDA margin below threshold",
            category="profitability",
            status=RuleStatus.TRIGGERED,
            value=-0.05,
            threshold=0.0,
        ),
        RuleResult(
            rule_id="R004",
            rule_name="Leverage above threshold",
            category="leverage",
            status=RuleStatus.TRIGGERED,
            value=6.0,
            threshold=5.0,
        ),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.CRITICAL