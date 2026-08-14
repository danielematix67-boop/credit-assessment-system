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


def test_credit_assessment_end_to_end():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    orchestrator = create_default_orchestrator()

    result = orchestrator.run(position)

    assert result.position_id == "POS001"
    assert result.assessment_status == AssessmentStatus.CRITICAL

    assert result.executive_summary
    assert result.findings
    assert isinstance(result.limitations, list)


def test_credit_assessment_propagates_comments_through_analysis_and_report():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

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

    triggered_comments = [
        finding.comment.text
        for finding in assessment.findings
        if finding.result.status == RuleStatus.TRIGGERED
    ]

    assert triggered_comments

    # The AnalysisAgent must consume the comments
    # associated with triggered rule findings.
    assert analysis.key_findings == triggered_comments

    # The deterministic report must preserve
    # the findings produced by the analysis layer.
    assert report.findings == analysis.key_findings

    # Therefore, the original rule comments must
    # reach the final report unchanged.
    assert report.findings == triggered_comments

    # Limitations must also propagate from the analysis
    # to the final report.
    assert report.limitations == analysis.limitations


def test_credit_assessment_llm_workflow():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=MockLLMClient(),
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

    # Findings and limitations remain deterministic
    # and are preserved by the LLM reporting workflow.
    assert result.report.findings == result.analysis.key_findings
    assert result.report.limitations == result.analysis.limitations


def test_llm_cannot_change_deterministic_assessment():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=MockLLMClient(),
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

    # Findings and limitations must remain deterministic.
    assert result.report.findings == result.analysis.key_findings
    assert result.report.limitations == result.analysis.limitations


def test_credit_assessment_falls_back_to_deterministic_report_when_llm_fails():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

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

    # The fallback report must preserve deterministic
    # findings and limitations.
    assert result.report.findings == result.analysis.key_findings
    assert result.report.limitations == result.analysis.limitations


def test_llm_cannot_replace_deterministic_findings():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

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

    # The report findings must come from the deterministic
    # assessment/analysis pipeline, not from the LLM.
    assert result.report.findings == result.analysis.key_findings

    assert (
        "The company shows severe financial deterioration."
        not in result.report.findings
    )


def test_llm_cannot_replace_deterministic_limitations():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

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
    assert result.report.limitations == result.analysis.limitations

def test_not_evaluable_rules_do_not_generate_findings():

    position = CreditPosition(
        position_id="POS_NORMAL",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=100000,
        ebitda_margin=0.15,
        pfn_to_ebitda=2.0,
        interest_expense=10000,
    )

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
    assert result.report.findings == []