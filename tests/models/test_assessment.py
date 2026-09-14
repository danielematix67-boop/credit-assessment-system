from src.comments.comment import Comment
from src.models.assessment_status import AssessmentStatus
from src.models.financial_assessment import FinancialAssessment
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_financial_assessment_preserves_data():
    result = RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test Rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )
    finding = RuleFinding(
        result=result,
        comment=Comment(rule_id="TEST_RULE", text="Test comment."),
    )
    assessment = FinancialAssessment(
        position_id="TEST_POSITION",
        rule_results=[result],
        findings=[finding],
        status=AssessmentStatus.ATTENTION,
    )
    assert assessment.rule_results == [result]
    assert assessment.findings == [finding]
    assert assessment.status == AssessmentStatus.ATTENTION


def test_financial_assessment_is_immutable():
    assessment = FinancialAssessment(
        position_id="TEST_POSITION",
        rule_results=[],
        findings=[],
        status=AssessmentStatus.NORMAL,
    )
    try:
        assessment.status = AssessmentStatus.CRITICAL
        raise AssertionError("FinancialAssessment must be immutable")
    except AttributeError:
        pass
