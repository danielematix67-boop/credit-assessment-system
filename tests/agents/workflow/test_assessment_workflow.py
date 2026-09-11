from unittest.mock import MagicMock

import pytest

from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.reporting.deterministic_report_generator import DeterministicReportGenerator
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.llm.mock_client import MockLLMClient
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report
from src.services.credit_assessment_case_service import CreditAssessmentCaseService


def make_position() -> CreditPosition:
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue=10_000_000.0,
        change_in_finished_goods_inventory=100_000.0,
        revenue_growth=0.05,
        ebitda=1_000_000.0,
        profit_loss=500_000.0,
        ebitda_margin=0.10,
        ebitda_inventory_contribution=0.20,
        nfp_to_ebitda=2.0,
        interest_expense=500_000.0,
    )


def build_workflow(assessment_service, reporting_agent) -> AssessmentWorkflow:
    return AssessmentWorkflow(
        credit_case_service=CreditAssessmentCaseService(assessment_service),
        case_analysis_agent=CaseAnalysisAgent(),
        reporting_agent=reporting_agent,
    )


def test_assessment_workflow_executes_case_pipeline(assessment_service):
    result = build_workflow(
        assessment_service,
        ReportingAgent(report_generator=DeterministicReportGenerator()),
    ).run(make_position())

    assert isinstance(result, AssessmentWorkflowResult)
    assert result.credit_case.position.position_id == "TEST_POSITION"
    assert result.analysis.position_id == "TEST_POSITION"
    assert result.report.position_id == "TEST_POSITION"
    assert (
        result.report.assessment_status.value
        == result.credit_case.final_assessment.status.value
    )


def test_assessment_workflow_preserves_domain_sections(assessment_service):
    result = build_workflow(
        assessment_service,
        ReportingAgent(report_generator=DeterministicReportGenerator()),
    ).run(make_position())

    section_names = [section.name for section in result.credit_case.sections]

    assert section_names == [
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    ]


def test_llm_cannot_override_deterministic_final_status(assessment_service):
    client = MockLLMClient(
        response=(
            "Assessment status: CRITICAL.\n"
            "The model claims a critical assessment despite the supplied evidence."
        )
    )
    workflow = build_workflow(
        assessment_service,
        ReportingAgent(
            report_generator=LLMReportGenerator(client),
            fallback_generator=DeterministicReportGenerator(),
        ),
    )

    result = workflow.run(make_position())
    expected_status = result.credit_case.final_assessment.status.value

    assert result.analysis.assessment_status.value == expected_status
    assert result.report.assessment_status.value == expected_status
    assert "Assessment Status: Critical" not in result.report.executive_summary
    assert expected_status.title() in result.report.executive_summary


def test_assessment_workflow_propagates_reporting_telemetry():
    reporting_agent = MagicMock()
    reporting_agent.run.return_value = MagicMock(spec=Report)
    reporting_agent.last_generator_used = "PRIMARY"
    reporting_agent.last_error = None
    reporting_agent.last_error_category = None

    case_service = MagicMock()
    case_analysis_agent = MagicMock()
    credit_case = MagicMock()
    analysis = MagicMock()
    report = reporting_agent.run.return_value
    case_service.assess.return_value = credit_case
    case_analysis_agent.run.return_value = analysis
    reporting_agent.run.return_value = report

    workflow = AssessmentWorkflow(
        credit_case_service=case_service,
        case_analysis_agent=case_analysis_agent,
        reporting_agent=reporting_agent,
    )

    result = workflow.run(make_position())

    assert result.report_generator_used == "PRIMARY"
    assert result.report_generation_error is None
    case_service.assess.assert_called_once()
    case_analysis_agent.run.assert_called_once_with(credit_case)
    reporting_agent.run.assert_called_once_with(analysis)


def test_assessment_workflow_propagates_terminal_reporting_failure():
    reporting_agent = MagicMock()
    reporting_agent.run.side_effect = RuntimeError("report generation failed")

    case_service = MagicMock()
    case_service.assess.return_value = MagicMock()
    case_analysis_agent = MagicMock()
    case_analysis_agent.run.return_value = MagicMock()

    workflow = AssessmentWorkflow(
        credit_case_service=case_service,
        case_analysis_agent=case_analysis_agent,
        reporting_agent=reporting_agent,
    )

    with pytest.raises(RuntimeError, match="report generation failed"):
        workflow.run(make_position())

    case_service.assess.assert_called_once()
    case_analysis_agent.run.assert_called_once()
    reporting_agent.run.assert_called_once()
