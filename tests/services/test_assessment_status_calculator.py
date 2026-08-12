import pytest

from src.models.assessment_status import AssessmentStatus
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import (
    AssessmentStatusCalculator,
)


def make_result(
    rule_id: str,
    status: RuleStatus,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Test rule {rule_id}",
        category="test",
        status=status,
        value=1.0 if status != RuleStatus.NOT_EVALUABLE else None,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.mark.parametrize(
    "results, expected_status",
    [
        (
            [],
            AssessmentStatus.NORMAL,
        ),
        (
            [
                make_result("R001", RuleStatus.NOT_TRIGGERED),
                make_result("R002", RuleStatus.NOT_TRIGGERED),
            ],
            AssessmentStatus.NORMAL,
        ),
        (
            [
                make_result("R001", RuleStatus.NOT_EVALUABLE),
                make_result("R002", RuleStatus.NOT_EVALUABLE),
            ],
            AssessmentStatus.NORMAL,
        ),
        (
            [
                make_result("R001", RuleStatus.TRIGGERED),
            ],
            AssessmentStatus.ATTENTION,
        ),
        (
            [
                make_result("R001", RuleStatus.TRIGGERED),
                make_result("R002", RuleStatus.NOT_EVALUABLE),
            ],
            AssessmentStatus.ATTENTION,
        ),
        (
            [
                make_result("R001", RuleStatus.TRIGGERED),
                make_result("R002", RuleStatus.TRIGGERED),
            ],
            AssessmentStatus.CRITICAL,
        ),
    ],
)
def test_assessment_status_calculator(
    results,
    expected_status,
):
    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == expected_status

def test_only_triggered_rules_affect_assessment_status():
    results = [
        make_result("R001", RuleStatus.TRIGGERED),
        make_result("R002", RuleStatus.NOT_EVALUABLE),
        make_result("R003", RuleStatus.NOT_TRIGGERED),
        make_result("R004", RuleStatus.NOT_EVALUABLE),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.ATTENTION

def test_not_evaluable_rules_do_not_count_as_triggered():
    results = [
        make_result("R001", RuleStatus.NOT_EVALUABLE),
        make_result("R002", RuleStatus.NOT_EVALUABLE),
        make_result("R003", RuleStatus.TRIGGERED),
    ]

    calculator = AssessmentStatusCalculator()

    status = calculator.calculate(results)

    assert status == AssessmentStatus.ATTENTION