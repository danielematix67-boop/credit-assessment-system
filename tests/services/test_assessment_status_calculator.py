import pytest

from src.models.assessment_status import AssessmentStatus
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import (
    AssessmentStatusCalculator,
)


def make_result(status: RuleStatus) -> RuleResult:
    return RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        status=status,
        value=(1.0 if status != RuleStatus.NOT_EVALUABLE else None),
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.mark.parametrize(
    "rule_statuses, expected_status",
    [
        ([], AssessmentStatus.NORMAL),
        ([RuleStatus.NOT_TRIGGERED], AssessmentStatus.NORMAL),
        (
            [RuleStatus.NOT_TRIGGERED, RuleStatus.NOT_TRIGGERED],
            AssessmentStatus.NORMAL,
        ),
        ([RuleStatus.NOT_EVALUABLE], AssessmentStatus.ATTENTION),
        (
            [RuleStatus.NOT_EVALUABLE, RuleStatus.NOT_EVALUABLE],
            AssessmentStatus.ATTENTION,
        ),
        ([RuleStatus.TRIGGERED], AssessmentStatus.ATTENTION),
        (
            [RuleStatus.TRIGGERED, RuleStatus.NOT_EVALUABLE],
            AssessmentStatus.ATTENTION,
        ),
        (
            [RuleStatus.TRIGGERED, RuleStatus.NOT_TRIGGERED],
            AssessmentStatus.ATTENTION,
        ),
        (
            [RuleStatus.TRIGGERED, RuleStatus.TRIGGERED],
            AssessmentStatus.CRITICAL,
        ),
        (
            [RuleStatus.TRIGGERED, RuleStatus.TRIGGERED, RuleStatus.NOT_EVALUABLE],
            AssessmentStatus.CRITICAL,
        ),
    ],
)
def test_assessment_status_is_derived_from_rule_statuses(
    rule_statuses,
    expected_status,
):
    results = [make_result(status) for status in rule_statuses]

    calculator = AssessmentStatusCalculator()

    assert calculator.calculate(results) == expected_status


@pytest.mark.parametrize(
    "non_triggered_status",
    [
        RuleStatus.NOT_TRIGGERED,
        RuleStatus.NOT_EVALUABLE,
    ],
)
def test_non_triggered_rules_do_not_affect_attention_status(
    non_triggered_status,
):
    results = [
        make_result(RuleStatus.TRIGGERED),
        make_result(non_triggered_status),
    ]

    calculator = AssessmentStatusCalculator()

    assert calculator.calculate(results) == AssessmentStatus.ATTENTION


@pytest.mark.parametrize(
    "additional_statuses",
    [
        [],
        [RuleStatus.NOT_TRIGGERED],
        [RuleStatus.NOT_EVALUABLE],
        [RuleStatus.NOT_TRIGGERED, RuleStatus.NOT_EVALUABLE],
    ],
)
def test_multiple_triggered_rules_remain_critical(
    additional_statuses,
):
    rule_statuses = [
        RuleStatus.TRIGGERED,
        RuleStatus.TRIGGERED,
        *additional_statuses,
    ]

    results = [make_result(status) for status in rule_statuses]

    calculator = AssessmentStatusCalculator()

    assert calculator.calculate(results) == AssessmentStatus.CRITICAL
