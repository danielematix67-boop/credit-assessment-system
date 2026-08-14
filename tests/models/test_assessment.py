import pytest

from src.comments.comment import Comment
from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@pytest.fixture
def rule_result():
    return RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test Rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.fixture
def comment():
    return Comment(
        rule_id="TEST_RULE",
        text="Test comment.",
    )


@pytest.fixture
def finding(rule_result, comment):
    return RuleFinding(
        result=rule_result,
        comment=comment,
    )


@pytest.fixture
def assessment(rule_result, finding):
    return Assessment(
        position_id="TEST_POSITION",
        rule_results=[rule_result],
        findings=[finding],
        status=AssessmentStatus.ATTENTION,
    )


def test_assessment_stores_provided_data(
    assessment,
    rule_result,
    finding,
):
    assert assessment.position_id == "TEST_POSITION"
    assert assessment.rule_results == [rule_result]
    assert assessment.findings == [finding]
    assert assessment.status == AssessmentStatus.ATTENTION


def test_assessment_preserves_rule_finding_relationship(
    assessment,
    rule_result,
    finding,
):
    assert assessment.rule_results[0] is rule_result
    assert assessment.findings[0] is finding
    assert assessment.findings[0].result is rule_result


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_assessment_accepts_valid_status(
    rule_result,
    finding,
    status,
):
    assessment = Assessment(
        position_id="TEST_POSITION",
        rule_results=[rule_result],
        findings=[finding],
        status=status,
    )

    assert assessment.status == status


def test_assessment_is_immutable(assessment):
    with pytest.raises(AttributeError):
        assessment.status = AssessmentStatus.CRITICAL