from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.llm.mock_client import MockLLMClient
from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.orchestration.orchestrator_factory import (
    create_default_orchestrator,
)
from src.rules.base.status import RuleStatus


def report_findings_by_category(report):
    """
    Convert the report's grouped findings into a dictionary
    keyed by category.

    This allows comparisons with AnalysisFinding objects
    without depending on the global ordering of categories.
    """
    return {
        group.category: group.findings
        for group in report.findings_by_category
    }


def analysis_findings_by_category(analysis):
    """
    Group analysis findings by category while preserving
    the order of findings within each category.
    """
    findings_by_category = {}

    for finding in analysis.key_findings:
        findings_by_category.setdefault(
            finding.category,
            [],
        ).append(finding)

    return findings_by_category


def make_critical_position() -> CreditPosition:
    return CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )


def make_normal_position() -> CreditPosition:
    return CreditPosition(
        position_id="POS_NORMAL",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=100000,
        ebitda_margin=0.15,
        pfn_to_ebitda=2.0,
        interest_expense=10000,
    )


def test_credit_assessment_end_to_end():
    position = make_critical_position()

    orchestrator = create_default_orchestrator()

    result = orchestrator.run(position)

    assert result.position_id == "POS001"
    assert result.assessment_status == AssessmentStatus.CRITICAL

    assert result.executive_summary
    assert result.findings_by_category
    assert isinstance(result.limitations, list)


def test_credit_assessment_propagates_findings_through_analysis_and_report():
    position = make_critical_position()

    workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    result = workflow.run(position)

    assessment = result.assessment
    analysis = result.analysis
    report = result.report

    # The assessment must contain findings generated
    # by the deterministic rule engine.
    assert assessment.findings

    triggered_findings = [
        finding
        for finding in assessment.findings
        if finding.result.status == RuleStatus.TRIGGERED
    ]

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

    # The AnalysisAgent must propagate both the category
    # and the comment text from the deterministic findings.
    assert actual_analysis_findings == expected_findings

    # The report groups findings by category.
    report_by_category = report_findings_by_category(report)
    analysis_by_category = analysis_findings_by_category(analysis)

    assert report_by_category == analysis_by_category

    # Verify that every deterministic finding reached the report.
    report_finding_pairs = [
        (
            finding.category,
            finding.text,
        )
        for findings in report_by_category.values()
        for finding in findings
    ]

    assert sorted(report_finding_pairs) == sorted(
        actual_analysis_findings
    )

    # Limitations must also propagate from the analysis
    # to the final report.
    assert report.limitations == analysis.limitations


def test_credit_assessment_llm_workflow():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response="CRITICAL assessment identified.",
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        LLMReportGenerator,
    )

    result = workflow.run(position)

    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None

    assert result.assessment.position_id == "POS001"
    assert result.analysis.position_id == "POS001"
    assert result.report.position_id == "POS001"

    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert result.report.executive_summary

    # The primary LLM generator must have been used.
    assert (
        workflow.reporting_agent.last_generator_used
        == "PRIMARY"
    )

    assert workflow.reporting_agent.last_error is None

    # Findings remain deterministic and structured.
    # The LLM must not modify them.
    assert (
        report_findings_by_category(result.report)
        == analysis_findings_by_category(result.analysis)
    )

    # Limitations remain deterministic.
    assert (
        result.report.limitations
        == result.analysis.limitations
    )


def test_llm_prompt_contains_assessment_and_safety_constraints():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response="CRITICAL assessment identified.",
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(position)

    assert result.report.executive_summary
    assert llm_client.last_prompt is not None

    prompt = llm_client.last_prompt

    # The deterministic assessment must be passed to the LLM.
    assert "Assessment status:" in prompt
    assert AssessmentStatus.CRITICAL.value in prompt
    assert "Key findings:" in prompt
    assert "Risk factors:" in prompt
    assert "Limitations:" in prompt

    # The LLM must operate exclusively on the structured
    # assessment provided by the deterministic pipeline.
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

    # Internal rule thresholds must not be exposed
    # through the executive summary.
    assert (
        "Do not disclose internal rule thresholds"
        in prompt
    )

    assert (
        "Do not reproduce threshold values"
        in prompt
    )


def test_llm_cannot_change_deterministic_assessment():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response=(
            "CRITICAL assessment identified. "
            "The company shows severe financial deterioration."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(position)

    # The assessment status is determined exclusively
    # by the deterministic assessment engine.
    assert result.assessment.status == AssessmentStatus.CRITICAL

    # The analysis must preserve the deterministic status.
    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    # The generated report must preserve the same status.
    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    # The LLM is only responsible for generating
    # the executive summary.
    assert result.report.executive_summary

    # Findings remain deterministic.
    assert (
        report_findings_by_category(result.report)
        == analysis_findings_by_category(result.analysis)
    )

    # Limitations remain deterministic.
    assert (
        result.report.limitations
        == result.analysis.limitations
    )


def test_llm_cannot_replace_deterministic_findings():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response=(
            "CRITICAL assessment identified. "
            "The company shows severe financial deterioration."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(position)

    # Report findings must come from the deterministic
    # assessment/analysis pipeline.
    assert (
        report_findings_by_category(result.report)
        == analysis_findings_by_category(result.analysis)
    )

    report_findings = [
        finding
        for findings in report_findings_by_category(
            result.report
        ).values()
        for finding in findings
    ]

    assert all(
        finding.text
        != "The company shows severe financial deterioration."
        for finding in report_findings
    )


def test_llm_cannot_replace_deterministic_limitations():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response=(
            "CRITICAL assessment identified. "
            "All relevant indicators were considered."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(position)

    # Limitations must remain those identified by
    # the deterministic assessment pipeline.
    assert (
        result.report.limitations
        == result.analysis.limitations
    )


def test_llm_response_is_rejected_when_empty():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response="   ",
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(position)

    # Empty LLM output must cause the deterministic
    # fallback generator to be used.
    assert result.report is not None

    assert (
        workflow.reporting_agent.last_generator_used
        == "FALLBACK"
    )

    assert (
        workflow.reporting_agent.last_error
        == "LLM report generation failed."
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )


def test_llm_response_is_rejected_when_status_is_missing():
    position = make_critical_position()

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

    result = workflow.run(position)

    # The response does not contain "CRITICAL".
    # Therefore, response validation must fail.
    assert result.report is not None

    assert (
        workflow.reporting_agent.last_generator_used
        == "FALLBACK"
    )

    assert (
        workflow.reporting_agent.last_error
        == "LLM report generation failed."
    )

    # The deterministic assessment remains authoritative.
    assert (
        result.assessment.status
        == AssessmentStatus.CRITICAL
    )

    assert (
        result.report.assessment_status
        == result.assessment.status
    )


def test_llm_response_is_accepted_when_status_is_present():
    position = make_critical_position()

    llm_client = MockLLMClient(
        response=(
            "The assessment status is CRITICAL. "
            "The assessment identifies significant "
            "financial weaknesses."
        ),
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=llm_client,
    )

    result = workflow.run(position)

    # The response passes validation and the primary
    # generator remains active.
    assert (
        workflow.reporting_agent.last_generator_used
        == "PRIMARY"
    )

    assert workflow.reporting_agent.last_error is None

    assert (
        result.report.executive_summary
        == llm_client.response
    )


def test_credit_assessment_falls_back_to_deterministic_report_when_llm_fails():
    position = make_critical_position()

    class FailingLLMClient:
        def generate(self, prompt: str) -> str:
            raise RuntimeError(
                "LLM service unavailable"
            )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=FailingLLMClient(),
    )

    result = workflow.run(position)

    # The deterministic assessment must remain valid.
    assert result.assessment.status == AssessmentStatus.CRITICAL

    # The analysis must preserve the deterministic assessment.
    assert (
        result.analysis.assessment_status
        == result.assessment.status
    )

    # A deterministic fallback report must still be generated.
    assert result.report is not None

    assert (
        result.report.assessment_status
        == result.assessment.status
    )

    assert result.report.position_id == "POS001"
    assert result.report.executive_summary

    # The fallback generator must have been used.
    assert (
        workflow.reporting_agent.last_generator_used
        == "FALLBACK"
    )

    assert (
        workflow.reporting_agent.last_error
        == "Gemini service is temporarily unavailable."
    )

    # The fallback report must preserve deterministic
    # findings and limitations.
    assert (
        report_findings_by_category(result.report)
        == analysis_findings_by_category(result.analysis)
    )

    assert (
        result.report.limitations
        == result.analysis.limitations
    )


def test_not_evaluable_rules_do_not_generate_findings():
    position = make_normal_position()

    workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    result = workflow.run(position)

    assert result.assessment.status == AssessmentStatus.NORMAL

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
        not_evaluable_rule_ids
    )

    assert result.analysis.key_findings == []

    assert (
        report_findings_by_category(result.report)
        == {}
    )
