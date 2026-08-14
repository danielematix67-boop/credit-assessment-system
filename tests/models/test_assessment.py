import pytest

from src.comments.comment import Comment
from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_assessment_stores_position_id_rule_results_findings_and_status():
    rule_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    comment = Comment(
        rule_id="R001",
        text=(
            "Revenue deterioration detected. "
            "Revenue growth: -15.0% (threshold: -10.0%)."
        ),
    )

    finding = RuleFinding(
        result=rule_result,
        comment=comment,
    )

    assessment = Assessment(
        position_id="POS001",
        rule_results=[rule_result],
        findings=[finding],
        status=AssessmentStatus.ATTENTION,
    )

    assert assessment.position_id == "POS001"
    assert assessment.rule_results == [rule_result]
    assert assessment.findings == [finding]
    assert assessment.status == AssessmentStatus.ATTENTION


def test_assessment_stores_complete_assessment_data():
    rule_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    comment = Comment(
        rule_id="R001",
        text="Revenue deterioration detected.",
    )

    finding = RuleFinding(
        result=rule_result,
        comment=comment,
    )

    assessment = Assessment(
        position_id="POS001",
        rule_results=[rule_result],
        findings=[finding],
        status=AssessmentStatus.ATTENTION,
    )

    assert assessment.position_id == "POS001"
    assert assessment.rule_results == [rule_result]
    assert assessment.findings == [finding]
    assert assessment.status == AssessmentStatus.ATTENTION


def test_assessment_is_immutable():
    assessment = Assessment(
        position_id="POS001",
        rule_results=[],
        findings=[],
        status=AssessmentStatus.NORMAL,
    )

    with pytest.raises(AttributeError):
        assessment.status = AssessmentStatus.CRITICAL