from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.base.agent import Agent
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)

def test_assessment_workflow_executes_all_stages(
    assessment_service,
):

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=AnalysisAgent(),
        reporting_agent=ReportingAgent(
            report_generator=DeterministicReportGenerator(),
        ),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    assert result.assessment.position_id == "POS001"
    assert result.analysis.position_id == "POS001"
    assert result.report.position_id == "POS001"

    assert result.report.assessment_status == (
        result.assessment.status
    )


def test_assessment_workflow_accepts_agent_contracts(
    assessment_service,
):

    class TestAnalysisAgent(
        Agent[Assessment, AssessmentAnalysis]
    ):

        def run(
            self,
            assessment: Assessment,
        ) -> AssessmentAnalysis:

            return AssessmentAnalysis(
                position_id=assessment.position_id,
                assessment_status=assessment.status,
                key_findings=["Test finding"],
                risk_factors=["Test risk"],
                limitations=[],
            )


    class TestReportingAgent(
        Agent[AssessmentAnalysis, Report]
    ):

        def run(
            self,
            analysis: AssessmentAnalysis,
        ) -> Report:

            return Report(
                position_id=analysis.position_id,
                assessment_status=analysis.assessment_status,
                executive_summary="Test summary",
                findings=analysis.key_findings,
                limitations=analysis.limitations,
            )


    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=TestAnalysisAgent(),
        reporting_agent=TestReportingAgent(),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    assert result.analysis.key_findings == [
        "Test finding",
    ]

    assert result.analysis.risk_factors == [
        "Test risk",
    ]

    assert result.report.executive_summary == "Test summary"