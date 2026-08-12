from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
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
        reporting_agent=ReportingAgent(),
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
        reporting_agent=ReportingAgent(),
    )

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    assessment = assessment_service.assess(position)
    report = orchestrator.run(position)

    assert report.assessment_status == assessment.status


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