# AnalysisAgent tests

import pytest

from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.base.agent import Agent
from src.comments.comment import Comment
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@pytest.fixture
def analysis_agent():
    return AnalysisAgent()


def make_rule_result(
    *,
    rule_id: str = "TEST_RULE",
    rule_name: str = "Test rule",
    category: str = "TEST_CATEGORY",
    status: RuleStatus = RuleStatus.TRIGGERED,
    severity: RuleSeverity = RuleSeverity.HIGH,
    value: float | None = None,
    threshold: float | None = None,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        status=status,
        value=value,
        threshold=threshold,
        severity=severity,
    )


def make_finding(
    result: RuleResult,
    text: str,
) -> RuleFinding:
    return RuleFinding(
        result=result,
        comment=Comment(
            rule_id=result.rule_id,
            text=text,
        ),
    )


def make_assessment(
    *,
    position_id: str = "TEST_POSITION",
    status: AssessmentStatus = AssessmentStatus.ATTENTION,
    rule_results: list[RuleResult],
    findings: list[RuleFinding],
) -> Assessment:
    return Assessment(
        position_id=position_id,
        status=status,
        rule_results=rule_results,
        findings=findings,
    )


def test_analysis_agent_implements_agent_contract(
    analysis_agent,
):
    assert isinstance(analysis_agent, Agent)


def test_analysis_agent_produces_structured_analysis(
    analysis_agent,
):
    triggered_results = [
        make_rule_result(
            rule_id="RULE_A",
            category="revenue",
            status=RuleStatus.TRIGGERED,
            severity=RuleSeverity.HIGH,
        ),
        make_rule_result(
            rule_id="RULE_B",
            category="profitability",
            status=RuleStatus.TRIGGERED,
            severity=RuleSeverity.HIGH,
        ),
    ]

    not_evaluable_result = make_rule_result(
        rule_id="RULE_C",
        rule_name="Unavailable metric",
        category="profitability",
        status=RuleStatus.NOT_EVALUABLE,
        severity=RuleSeverity.MEDIUM,
    )

    triggered_comments = [
        "First triggered finding.",
        "Second triggered finding.",
    ]

    findings = [
        make_finding(
            triggered_results[0],
            triggered_comments[0],
        ),
        make_finding(
            triggered_results[1],
            triggered_comments[1],
        ),
    ]

    assessment = make_assessment(
        status=AssessmentStatus.CRITICAL,
        rule_results=[
            *triggered_results,
            not_evaluable_result,
        ],
        findings=findings,
    )

    analysis = analysis_agent.run(assessment)

    assert isinstance(analysis, AssessmentAnalysis)
    assert analysis.position_id == assessment.position_id
    assert analysis.assessment_status == assessment.status

    assert all(
        isinstance(finding, AnalysisFinding)
        for finding in analysis.key_findings
    )

    assert [finding.text for finding in analysis.key_findings] == (
        triggered_comments
    )

    assert [finding.rule_id for finding in analysis.key_findings] == [
        result.rule_id
        for result in triggered_results
    ]

    assert [finding.category for finding in analysis.key_findings] == [
        result.category
        for result in triggered_results
    ]

    assert [finding.severity for finding in analysis.key_findings] == [
        result.severity
        for result in triggered_results
    ]

    assert [finding.text for finding in analysis.risk_factors] == (
        triggered_comments
    )

    assert [finding.rule_id for finding in analysis.risk_factors] == [
        result.rule_id
        for result in triggered_results
    ]

    assert [finding.category for finding in analysis.risk_factors] == [
        result.category
        for result in triggered_results
    ]

    assert [finding.severity for finding in analysis.risk_factors] == [
        result.severity
        for result in triggered_results
    ]

    assert [finding.text for finding in analysis.limitations] == [
        not_evaluable_result.rule_name
    ]

    assert [finding.rule_id for finding in analysis.limitations] == [
        not_evaluable_result.rule_id
    ]

    assert [finding.category for finding in analysis.limitations] == [
        not_evaluable_result.category
    ]

    assert [finding.severity for finding in analysis.limitations] == [
        not_evaluable_result.severity
    ]


def test_analysis_agent_uses_comment_text_for_key_findings(
    analysis_agent,
):
    result = make_rule_result(
        rule_id="CUSTOM_RULE",
        category="custom_category",
        status=RuleStatus.TRIGGERED,
        severity=RuleSeverity.MEDIUM,
    )

    comment_text = "Custom finding generated by the comment engine."

    finding = make_finding(
        result,
        comment_text,
    )

    assessment = make_assessment(
        rule_results=[result],
        findings=[finding],
    )

    analysis = analysis_agent.run(assessment)

    assert len(analysis.key_findings) == 1

    analysis_finding = analysis.key_findings[0]

    assert analysis_finding.text == comment_text
    assert analysis_finding.rule_id == result.rule_id
    assert analysis_finding.category == result.category
    assert analysis_finding.severity == result.severity


def test_analysis_agent_uses_comment_text_for_risk_factors(
    analysis_agent,
):
    result = make_rule_result(
        rule_id="CUSTOM_RULE",
        category="custom_category",
        status=RuleStatus.TRIGGERED,
        severity=RuleSeverity.HIGH,
    )

    comment_text = "Custom high-severity risk identified."

    finding = make_finding(
        result,
        comment_text,
    )

    assessment = make_assessment(
        status=AssessmentStatus.CRITICAL,
        rule_results=[result],
        findings=[finding],
    )

    analysis = analysis_agent.run(assessment)

    assert len(analysis.risk_factors) == 1

    risk_factor = analysis.risk_factors[0]

    assert risk_factor.text == comment_text
    assert risk_factor.rule_id == result.rule_id
    assert risk_factor.category == result.category
    assert risk_factor.severity == RuleSeverity.HIGH


def test_analysis_agent_does_not_depend_on_rule_ids(
    analysis_agent,
):
    results = [
        make_rule_result(
            rule_id="ARBITRARY_ID_A",
            category="category_a",
            status=RuleStatus.TRIGGERED,
            severity=RuleSeverity.HIGH,
        ),
        make_rule_result(
            rule_id="COMPLETELY_DIFFERENT_ID",
            category="category_b",
            status=RuleStatus.TRIGGERED,
            severity=RuleSeverity.MEDIUM,
        ),
    ]

    comments = [
        "First arbitrary finding.",
        "Second arbitrary finding.",
    ]

    findings = [
        make_finding(results[0], comments[0]),
        make_finding(results[1], comments[1]),
    ]

    assessment = make_assessment(
        rule_results=results,
        findings=findings,
    )

    analysis = analysis_agent.run(assessment)

    assert analysis.assessment_status == assessment.status

    assert [finding.text for finding in analysis.key_findings] == (
        comments
    )

    assert [finding.rule_id for finding in analysis.key_findings] == [
        result.rule_id
        for result in results
    ]

    assert [finding.category for finding in analysis.key_findings] == [
        result.category
        for result in results
    ]

    assert [finding.text for finding in analysis.risk_factors] == [
        comments[0]
    ]


def test_analysis_agent_ignores_not_triggered_rules(
    analysis_agent,
):
    triggered_result = make_rule_result(
        rule_id="TRIGGERED_RULE",
        category="triggered_category",
        status=RuleStatus.TRIGGERED,
        severity=RuleSeverity.HIGH,
    )

    not_triggered_result = make_rule_result(
        rule_id="NOT_TRIGGERED_RULE",
        category="ignored_category",
        status=RuleStatus.NOT_TRIGGERED,
        severity=RuleSeverity.LOW,
    )

    triggered_comment = "Triggered finding."

    assessment = make_assessment(
        rule_results=[
            triggered_result,
            not_triggered_result,
        ],
        findings=[
            make_finding(
                triggered_result,
                triggered_comment,
            ),
        ],
    )

    analysis = analysis_agent.run(assessment)

    assert [
        finding.text for finding in analysis.key_findings
    ] == [triggered_comment]

    assert [
        finding.rule_id for finding in analysis.key_findings
    ] == [triggered_result.rule_id]

    assert [
        finding.text for finding in analysis.risk_factors
    ] == [triggered_comment]

    assert analysis.limitations == []


def test_analysis_agent_handles_normal_assessment(
    analysis_agent,
):
    results = [
        make_rule_result(
            status=RuleStatus.NOT_TRIGGERED,
            severity=RuleSeverity.LOW,
        ),
        make_rule_result(
            status=RuleStatus.NOT_TRIGGERED,
            severity=RuleSeverity.LOW,
        ),
    ]

    assessment = make_assessment(
        status=AssessmentStatus.NORMAL,
        rule_results=results,
        findings=[],
    )

    analysis = analysis_agent.run(assessment)

    assert analysis.position_id == assessment.position_id
    assert analysis.assessment_status == assessment.status
    assert analysis.key_findings == []
    assert analysis.risk_factors == []
    assert analysis.limitations == []


def test_analysis_agent_reports_not_evaluable_rules_as_limitations(
    analysis_agent,
):
    results = [
        make_rule_result(
            rule_id="UNAVAILABLE_A",
            rule_name="Unavailable revenue metric",
            category="revenue",
            status=RuleStatus.NOT_EVALUABLE,
            severity=RuleSeverity.MEDIUM,
        ),
        make_rule_result(
            rule_id="UNAVAILABLE_B",
            rule_name="Unavailable profitability metric",
            category="profitability",
            status=RuleStatus.NOT_EVALUABLE,
            severity=RuleSeverity.LOW,
        ),
    ]

    assessment = make_assessment(
        status=AssessmentStatus.NORMAL,
        rule_results=results,
        findings=[],
    )

    analysis = analysis_agent.run(assessment)

    assert analysis.key_findings == []
    assert analysis.risk_factors == []

    assert [finding.text for finding in analysis.limitations] == [
        result.rule_name
        for result in results
    ]

    assert [finding.rule_id for finding in analysis.limitations] == [
        result.rule_id
        for result in results
    ]

    assert [finding.category for finding in analysis.limitations] == [
        result.category
        for result in results
    ]

    assert [finding.severity for finding in analysis.limitations] == [
        result.severity
        for result in results
    ]


@pytest.mark.parametrize(
    "severity, expected_as_risk_factor",
    [
        (RuleSeverity.HIGH, True),
        (RuleSeverity.MEDIUM, False),
        (RuleSeverity.LOW, False),
    ],
)
def test_analysis_agent_selects_high_severity_risk_factors(
    analysis_agent,
    severity,
    expected_as_risk_factor,
):
    result = make_rule_result(
        status=RuleStatus.TRIGGERED,
        severity=severity,
    )

    comment_text = f"Risk associated with {severity.value} severity."

    assessment = make_assessment(
        status=AssessmentStatus.CRITICAL,
        rule_results=[result],
        findings=[
            make_finding(
                result,
                comment_text,
            ),
        ],
    )

    analysis = analysis_agent.run(assessment)

    assert [finding.text for finding in analysis.key_findings] == [
        comment_text
    ]

    expected_risk_factors = (
        analysis.key_findings
        if expected_as_risk_factor
        else []
    )

    assert analysis.risk_factors == expected_risk_factors