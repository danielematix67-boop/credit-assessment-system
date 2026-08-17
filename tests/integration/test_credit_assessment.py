import pytest

from src.agents.reporting.llm_report_generator import (
    LLMReportGenerator,
)
from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.llm.mock_client import MockLLMClient
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def risk_position() -> CreditPosition:
    """
    Return a position designed to produce a non-normal
    deterministic assessment.

    The fixture uses economically meaningful values but the
    tests do not depend on specific rule IDs.
    """
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )


@pytest.fixture
def normal_position() -> CreditPosition:
    """
    Return a position expected to produce a normal assessment.
    """
    return CreditPosition(
        position_id="TEST_NORMAL_POSITION",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=100000,
        ebitda_margin=0.15,
        pfn_to_ebitda=2.0,
        interest_expense=10000,
    )


# ============================================================
# Helpers
# ============================================================


def report_findings_by_category(report):
    """
    Group report findings by category.

    Category ordering is intentionally ignored.
    """
    return {
        group.category: group.findings
        for group in report.findings_by_category
    }


def analysis_findings_by_category(analysis):
    """
    Group analysis findings by category.

    The order of findings within each category is preserved.
    """
    findings_by_category = {}

    for finding in analysis.key_findings:
        findings_by_category.setdefault(
            finding.category,
            [],
        ).append(finding)

    return findings_by_category


def deterministic_findings(assessment):
    """
    Return all findings produced by the deterministic
    assessment pipeline.
    """
    return [
        finding
        for finding in assessment.findings
        if finding.result.status == RuleStatus.TRIGGERED
    ]


def finding_pairs(findings):
    """
    Return the semantic content of findings without relying
    on concrete object instances.
    """
    return [
        (
            finding.category,
            finding.text,
        )
        for finding in findings
    ]


def assert_deterministic_information_is_preserved(result):
    """
    Verify that deterministic information remains unchanged
    throughout the assessment pipeline.
    """
    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None

    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert (
        report_findings_by_category(result.report)
        == analysis_findings_by_category(result.analysis)
    )

    assert (
        result.report.limitations
        == result.analysis.limitations
    )


def make_valid_llm_response(status):
    """
    Generate a minimal LLM response that satisfies the
    report validation contract.

    The status is derived from the deterministic assessment
    rather than hard-coded in the test.
    """
    return (
        f"The assessment status is {status.value}. "
        "The assessment identifies the relevant financial "
        "risk factors based on the available information."
    )


# ============================================================
# End-to-end deterministic workflow
# ============================================================


def test_credit_assessment_end_to_end(risk_position):
    workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    result = workflow.run(risk_position)

    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None

    assert (
        result.assessment.position_id
        == risk_position.position_id
    )

    assert (
        result.analysis.position_id
        == risk_position.position_id
    )

    assert (
        result.report.position_id
        == risk_position.position_id
    )

    assert result.assessment.status is not None

    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert result.report.executive_summary
    assert isinstance(result.report.limitations, list)


def test_credit_assessment_propagates_findings_through_pipeline(
    risk_position,
):
    workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    result = workflow.run(risk_position)

    assessment = result.assessment
    analysis = result.analysis
    report = result.report

    assert assessment.findings

    triggered_findings = deterministic_findings(
        assessment,
    )

    assert triggered_findings

    expected_findings = [
        (
            finding.result.category,
            finding.comment.text,
        )
        for finding in triggered_findings
    ]

    actual_analysis_findings = [
        (
            finding.category,
            finding.text,
        )
        for finding in analysis.key_findings
    ]

    assert actual_analysis_findings == expected_findings

    report_by_category = report_findings_by_category(
        report,
    )

    analysis_by_category = analysis_findings_by_category(
        analysis,
    )

    assert report_by_category == analysis_by_category

    report_finding_pairs = [
        (
            finding.category,
            finding.text,
        )
        for findings in report_by_category.values()
        for finding in findings
    ]

    assert sorted(report_finding_pairs) == sorted(
        actual_analysis_findings,
    )

    assert report.limitations == analysis.limitations


# ============================================================
# LLM workflow
# ============================================================


def test_llm_workflow_uses_primary_generator(
    risk_position,
):
    """
    Verify that a valid LLM response is handled by the primary
    generator rather than the deterministic fallback.

    The LLM is mocked, so this test does not require Ollama.
    """
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    expected_status = deterministic_result.assessment.status

    llm_client = MockLLMClient(
        response=make_valid_llm_response(
            expected_status,
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        LLMReportGenerator,
    )

    result = workflow.run(risk_position)

    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None

    assert (
        result.assessment.position_id
        == risk_position.position_id
    )

    assert (
        result.analysis.position_id
        == risk_position.position_id
    )

    assert (
        result.report.position_id
        == risk_position.position_id
    )

    assert (
        result.assessment.status
        == expected_status
    )

    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert result.report.executive_summary

    assert (
        workflow.reporting_agent.last_generator_used
        == "PRIMARY"
    )

    assert workflow.reporting_agent.last_error is None


def test_credit_assessment_llm_workflow(
    risk_position,
):
    """
    Verify that the complete assessment workflow can use an
    LLM report generator while preserving deterministic data.

    The LLM is mocked, so this test does not require Ollama.
    """
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    llm_client = MockLLMClient(
        response=make_valid_llm_response(
            deterministic_result.assessment.status,
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert isinstance(
        workflow.reporting_agent.report_generator,
        LLMReportGenerator,
    )

    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None

    assert_deterministic_information_is_preserved(
        result,
    )

    assert result.report.executive_summary

    assert (
        workflow.reporting_agent.last_generator_used
        == "PRIMARY"
    )

    assert workflow.reporting_agent.last_error is None


def test_llm_workflow_sends_prompt_to_llm_client(
    risk_position,
):
    """
    Verify that the LLM workflow actually sends a prompt to
    the configured LLM client.

    The client is mocked, so Ollama is not executed.
    """
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    llm_client = MockLLMClient(
        response=make_valid_llm_response(
            deterministic_result.assessment.status,
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    workflow.run(risk_position)

    assert llm_client.last_prompt is not None
    assert llm_client.last_prompt.strip()

    assert (
        "Assessment status:"
        in llm_client.last_prompt
    )


# ============================================================
# LLM prompt
# ============================================================


def test_llm_prompt_contains_assessment_and_safety_constraints(
    risk_position,
):
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    llm_client = MockLLMClient(
        response=make_valid_llm_response(
            deterministic_result.assessment.status,
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert result.report.executive_summary
    assert llm_client.last_prompt is not None

    prompt = llm_client.last_prompt

    assert "Assessment status:" in prompt

    assert (
        deterministic_result.assessment.status.value
        in prompt
    )

    assert "Key findings:" in prompt
    assert "Risk factors:" in prompt
    assert "Limitations:" in prompt

    assert (
        "Do not introduce facts that are not present"
        in prompt
    )

    assert (
        "Do not invent financial data"
        in prompt
    )

    assert (
        "Do not modify the assessment status"
        in prompt
    )

    assert (
        "Do not make a credit decision"
        in prompt
    )

    assert (
        "If information is missing or not evaluable"
        in prompt
    )

    assert (
        "Do not disclose internal rule thresholds"
        in prompt
    )

    assert (
        "Do not reproduce threshold values"
        in prompt
    )


# ============================================================
# LLM cannot modify deterministic assessment
# ============================================================


def test_llm_cannot_change_deterministic_assessment(
    risk_position,
):
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    expected_status = deterministic_result.assessment.status

    llm_client = MockLLMClient(
        response=(
            f"The assessment status is {expected_status.value}. "
            "The company shows severe financial deterioration."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert (
        result.assessment.status
        == expected_status
    )

    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert result.report.executive_summary

    assert_deterministic_information_is_preserved(
        result,
    )


# ============================================================
# LLM cannot replace deterministic findings
# ============================================================


def test_llm_cannot_replace_deterministic_findings(
    risk_position,
):
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    expected_status = deterministic_result.assessment.status

    fabricated_finding = (
        "The company shows severe financial deterioration."
    )

    llm_client = MockLLMClient(
        response=(
            f"The assessment status is {expected_status.value}. "
            f"{fabricated_finding}"
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert (
        report_findings_by_category(result.report)
        == analysis_findings_by_category(result.analysis)
    )

    report_findings = [
        finding
        for findings in report_findings_by_category(
            result.report,
        ).values()
        for finding in findings
    ]

    assert all(
        finding.text != fabricated_finding
        for finding in report_findings
    )


# ============================================================
# LLM cannot replace deterministic limitations
# ============================================================


def test_llm_cannot_replace_deterministic_limitations(
    risk_position,
):
    deterministic_workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    deterministic_result = deterministic_workflow.run(
        risk_position,
    )

    expected_status = deterministic_result.assessment.status

    llm_client = MockLLMClient(
        response=(
            f"The assessment status is {expected_status.value}. "
            "All relevant indicators were considered."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert (
        result.report.limitations
        == result.analysis.limitations
    )


# ============================================================
# LLM response validation
# ============================================================


def test_llm_response_is_rejected_when_empty(
    risk_position,
):
    llm_client = MockLLMClient(
        response="   ",
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert result.report is not None

    assert (
        workflow.reporting_agent.last_generator_used
        == "FALLBACK"
    )

    assert (
        workflow.reporting_agent.last_error
        == (
            "LLM report generation failed: "
            "LLM returned an empty response"
        )
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )


def test_llm_response_is_rejected_when_status_is_missing(
    risk_position,
):
    llm_client = MockLLMClient(
        response=(
            "The company shows significant financial "
            "deterioration and elevated risk."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert result.report is not None

    assert (
        workflow.reporting_agent.last_generator_used
        == "FALLBACK"
    )

    assert (
        workflow.reporting_agent.last_error
        == (
            "LLM report generation failed: "
            "LLM response does not contain the assessment status"
        )
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )


# ============================================================
# LLM failure and deterministic fallback
# ============================================================


def test_credit_assessment_falls_back_to_deterministic_report_when_llm_fails(
    risk_position,
):
    """
    Verify that an LLM failure causes the workflow to use the
    deterministic fallback report generator.

    The failing client is mocked; Ollama is not executed.
    """
    llm_client = MockLLMClient(
        error=RuntimeError(
            "LLM service unavailable",
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(risk_position)

    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None

    assert (
        result.assessment.status
        == result.analysis.assessment_status
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert (
        result.report.position_id
        == risk_position.position_id
    )

    assert result.report.executive_summary

    assert (
        workflow.reporting_agent.last_generator_used
        == "FALLBACK"
    )

    assert (
        workflow.reporting_agent.last_error
        == "LLM service is temporarily unavailable."
    )

    assert_deterministic_information_is_preserved(
        result,
    )


# ============================================================
# NOT_EVALUABLE rules
# ============================================================


def test_not_evaluable_rules_do_not_generate_findings(
    normal_position,
):
    workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    result = workflow.run(normal_position)

    not_evaluable_results = [
        rule_result
        for rule_result in result.assessment.rule_results
        if rule_result.status == RuleStatus.NOT_EVALUABLE
    ]

    assert not_evaluable_results

    not_evaluable_rule_ids = {
        rule_result.rule_id
        for rule_result in not_evaluable_results
    }

    finding_rule_ids = {
        finding.result.rule_id
        for finding in result.assessment.findings
    }

    assert finding_rule_ids.isdisjoint(
        not_evaluable_rule_ids,
    )

    assert result.analysis.key_findings == []

    assert (
        report_findings_by_category(result.report)
        == {}
    )