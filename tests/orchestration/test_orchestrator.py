from unittest.mock import Mock

from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.assessment_status import AssessmentStatus
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report
from src.orchestration.orchestrator import AssessmentOrchestrator
from src.orchestration.orchestrator_factory import (
    create_default_orchestrator,
)


def test_orchestrator_returns_report(assessment_service):
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

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    report = orchestrator.run(position)

    assert isinstance(report, Report)
    assert report.position_id == position.position_id


def test_orchestrator_preserves_assessment_status(assessment_service):
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

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    assessment = assessment_service.assess(position)
    report = orchestrator.run(position)

    assert report.assessment_status == assessment.status


def test_orchestrator_delegates_execution_to_workflow():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    expected_report = Mock(spec=Report)

    workflow = Mock(spec=AssessmentWorkflow)

    workflow.run.return_value = AssessmentWorkflowResult(
        assessment=None,
        analysis=None,
        report=expected_report,
    )

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    result = orchestrator.run(position)

    workflow.run.assert_called_once_with(position)

    assert result is expected_report


def test_default_orchestrator_creates_valid_orchestrator():
    orchestrator = create_default_orchestrator()

    assert isinstance(
        orchestrator,
        AssessmentOrchestrator,
    )

    assert isinstance(
        orchestrator.workflow,
        AssessmentWorkflow,
    )

    assert isinstance(
        orchestrator.workflow.analysis_agent,
        AnalysisAgent,
    )

    assert isinstance(
        orchestrator.workflow.reporting_agent,
        ReportingAgent,
    )


def test_orchestrator_depends_only_on_workflow():

    class TestWorkflow:

        def run(self, position):

            return AssessmentWorkflowResult(
                assessment=None,
                analysis=None,
                report=Report(
                    position_id=position.position_id,
                    assessment_status=AssessmentStatus.NORMAL,
                    executive_summary="Test summary",
                    findings=[],
                    limitations=[],
                ),
            )

    workflow = TestWorkflow()

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.10,
        ebitda=100000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=2.0,
        interest_expense=20000,
    )

    report = orchestrator.run(position)

    assert isinstance(report, Report)
    assert report.position_id == "POS001"
    assert report.executive_summary == "Test summary"