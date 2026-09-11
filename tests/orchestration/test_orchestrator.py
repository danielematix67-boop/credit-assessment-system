from unittest.mock import Mock

import pytest

from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.models.report import Report, ReportFindingGroup
from src.orchestration.orchestrator import AssessmentOrchestrator
from src.orchestration.orchestrator_factory import (
    create_default_orchestrator,
)


@pytest.fixture
def normal_position():
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=0.10,
        ebitda=100000,
        profit_loss=50000,
        ebitda_margin=0.10,
        nfp_to_ebitda=2.0,
        interest_expense=20000,
    )


@pytest.fixture
def critical_position():
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        nfp_to_ebitda=6.0,
        interest_expense=40000,
    )


@pytest.fixture
def deterministic_workflow(assessment_service):
    from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
    from src.services.credit_assessment_case_service import CreditAssessmentCaseService

    return AssessmentWorkflow(
        credit_case_service=CreditAssessmentCaseService(assessment_service),
        case_analysis_agent=CaseAnalysisAgent(),
        reporting_agent=ReportingAgent(
            report_generator=DeterministicReportGenerator(),
        ),
    )


@pytest.fixture
def orchestrator(deterministic_workflow):
    return AssessmentOrchestrator(
        workflow=deterministic_workflow,
    )


def test_orchestrator_returns_report(
    orchestrator,
    critical_position,
):
    report = orchestrator.run(critical_position)

    assert isinstance(report, Report)
    assert report.position_id == critical_position.position_id


def test_orchestrator_preserves_assessment_status(
    assessment_service,
    orchestrator,
    critical_position,
):
    expected_status = assessment_service.assess(critical_position).status

    report = orchestrator.run(critical_position)

    assert report.assessment_status == expected_status


def _workflow_result(report):
    return AssessmentWorkflowResult(
        credit_case=Mock(spec=CreditAssessmentCase),
        analysis=Mock(spec=AssessmentAnalysis),
        report=report,
    )


def test_orchestrator_delegates_execution_to_workflow():
    position = Mock(spec=CreditPosition)
    expected_report = Mock(spec=Report)

    workflow = Mock(spec=AssessmentWorkflow)
    workflow.run.return_value = _workflow_result(expected_report)

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
        CaseAnalysisAgent,
    )

    assert isinstance(
        orchestrator.workflow.reporting_agent,
        ReportingAgent,
    )


def test_orchestrator_depends_only_on_workflow():
    position = Mock(spec=CreditPosition)
    expected_report = Mock(spec=Report)

    workflow = Mock(spec=AssessmentWorkflow)
    workflow.run.return_value = _workflow_result(expected_report)

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    result = orchestrator.run(position)

    workflow.run.assert_called_once_with(position)

    assert result is expected_report


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_orchestrator_preserves_report_status(
    status,
):
    position = Mock(spec=CreditPosition)
    expected_report = Report(
        position_id="TEST_POSITION",
        assessment_status=status,
        executive_summary="Generated report",
        findings_by_category=[],
        limitations=[],
    )

    workflow = Mock(spec=AssessmentWorkflow)
    workflow.run.return_value = _workflow_result(expected_report)

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    report = orchestrator.run(position)

    assert report.assessment_status == status


@pytest.mark.parametrize(
    "findings_by_category",
    [
        [],
        [
            ReportFindingGroup(
                category="category",
                findings=[],
            ),
        ],
        [
            ReportFindingGroup(
                category="category_a",
                findings=[],
            ),
            ReportFindingGroup(
                category="category_b",
                findings=[],
            ),
        ],
        [
            ReportFindingGroup(
                category="category_a",
                findings=[],
            ),
            ReportFindingGroup(
                category="category_b",
                findings=[],
            ),
            ReportFindingGroup(
                category="category_c",
                findings=[],
            ),
        ],
    ],
)
def test_orchestrator_preserves_findings_by_category(
    findings_by_category,
):
    position = Mock(spec=CreditPosition)

    expected_report = Report(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.NORMAL,
        executive_summary="Generated report",
        findings_by_category=findings_by_category,
        limitations=[],
    )

    workflow = Mock(spec=AssessmentWorkflow)
    workflow.run.return_value = _workflow_result(expected_report)

    orchestrator = AssessmentOrchestrator(
        workflow=workflow,
    )

    report = orchestrator.run(position)

    workflow.run.assert_called_once_with(position)

    assert report.findings_by_category == findings_by_category
