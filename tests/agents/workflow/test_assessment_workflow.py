from unittest.mock import MagicMock

import pytest

from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.base.agent import Agent
from src.agents.reporting.deterministic_report_generator import DeterministicReportGenerator
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.llm.mock_client import MockLLMClient
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report
from src.services.credit_assessment_case_service import CreditAssessmentCaseService
from src.rules.base.severity import RuleSeverity


# ============================================================
# Helpers
# ============================================================


def make_position() -> CreditPosition:
    """Create a generic fully evaluable, risk-free financial test position."""
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


def make_report(
    position_id: str,
    assessment_status,
) -> Report:
    """Create a minimal report suitable for workflow tests."""
    return Report(
        position_id=position_id,
        assessment_status=assessment_status,
        executive_summary="Test summary",
        findings_by_category=[],
        limitations=[],
    )


# ============================================================
# Workflow execution
# ============================================================


def test_assessment_workflow_executes_all_stages(
    assessment_service,
):
    position = make_position()

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=AnalysisAgent(),
        reporting_agent=ReportingAgent(
            report_generator=DeterministicReportGenerator(),
        ),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    assert result.assessment.position_id == position.position_id
    assert result.analysis.position_id == position.position_id
    assert result.report.position_id == position.position_id

    assert result.report.assessment_status == (result.assessment.status)

    assert result.report_generator_used == "PRIMARY"
    assert result.report_generation_error is None


def test_assessment_workflow_integrates_credit_case_pipeline(
    assessment_service,
):
    position = make_position()
    case_service = CreditAssessmentCaseService(assessment_service)

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=AnalysisAgent(),
        reporting_agent=ReportingAgent(
            report_generator=DeterministicReportGenerator(),
        ),
        credit_case_service=case_service,
        case_analysis_agent=CaseAnalysisAgent(),
    )

    result = workflow.run(position)

    assert result.credit_case is not None
    assert result.credit_case.position.position_id == position.position_id

    assert result.assessment.position_id == position.position_id
    assert result.assessment.rule_results == result.credit_case.financial_analysis.evidence
    assert result.assessment.findings == result.credit_case.financial_analysis.findings
    assert result.assessment.status.value == result.credit_case.financial_analysis.status.value

    assert result.analysis.assessment_status.value == result.credit_case.final_assessment.status.value
    assert result.report.assessment_status == result.analysis.assessment_status


def test_assessment_workflow_llm_cannot_override_deterministic_status(
    assessment_service,
):
    """An adversarial LLM status must never replace the deterministic status."""
    position = make_position()
    deterministic_assessment = assessment_service.assess(position)

    client = MockLLMClient(
        response=(
            "Assessment status: CRITICAL.\n"
            "The model claims a critical assessment despite the supplied evidence."
        )
    )
    llm_generator = LLMReportGenerator(client)

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=AnalysisAgent(),
        reporting_agent=ReportingAgent(
            report_generator=llm_generator,
            fallback_generator=DeterministicReportGenerator(),
        ),
    )

    result = workflow.run(position)

    assert deterministic_assessment.status.value == "NORMAL"
    assert result.assessment.status == deterministic_assessment.status
    assert result.analysis.assessment_status == deterministic_assessment.status
    assert result.report.assessment_status == deterministic_assessment.status
    assert "Assessment Status: Critical" not in result.report.executive_summary
    assert "Assessment Status: Normal" in result.report.executive_summary


# ============================================================
# Agent contract compatibility
# ============================================================


def test_assessment_workflow_accepts_agent_contracts(
    assessment_service,
):
    class TestAnalysisAgent(Agent[Assessment, AssessmentAnalysis]):
        def run(
            self,
            assessment: Assessment,
        ) -> AssessmentAnalysis:
            return AssessmentAnalysis(
                position_id=assessment.position_id,
                assessment_status=assessment.status,
                key_findings=[
                    AnalysisFinding(
                        rule_id="GENERIC_RULE",
                        category="GENERIC_CATEGORY",
                        severity=RuleSeverity.HIGH,
                        text="Generic finding",
                    ),
                ],
                risk_factors=[
                    AnalysisFinding(
                        rule_id="GENERIC_RULE",
                        category="GENERIC_CATEGORY",
                        severity=RuleSeverity.HIGH,
                        text="Generic risk",
                    ),
                ],
                limitations=[],
            )

    class TestReportingAgent(Agent[AssessmentAnalysis, Report]):
        def run(
            self,
            analysis: AssessmentAnalysis,
        ) -> Report:
            return make_report(
                position_id=analysis.position_id,
                assessment_status=analysis.assessment_status,
            )

    position = make_position()

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=TestAnalysisAgent(),
        reporting_agent=TestReportingAgent(),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    assert result.assessment.position_id == position.position_id
    assert result.analysis.position_id == position.position_id
    assert result.report.position_id == position.position_id

    assert result.analysis.assessment_status == (result.assessment.status)

    assert result.report.assessment_status == (result.analysis.assessment_status)

    assert len(result.analysis.key_findings) == 1
    assert len(result.analysis.risk_factors) == 1

    assert isinstance(
        result.analysis.key_findings[0],
        AnalysisFinding,
    )

    assert isinstance(
        result.analysis.risk_factors[0],
        AnalysisFinding,
    )

    assert result.analysis.limitations == []

    assert result.report_generator_used is None
    assert result.report_generation_error is None


# ============================================================
# Reporting telemetry propagation
# ============================================================


def test_assessment_workflow_propagates_primary_reporting_status():
    reporting_agent = MagicMock()

    reporting_agent.run.return_value = MagicMock(
        spec=Report,
    )

    reporting_agent.last_generator_used = "PRIMARY"
    reporting_agent.last_error = None

    assessment_service = MagicMock()
    analysis_agent = MagicMock()

    assessment = MagicMock(spec=Assessment)
    analysis = MagicMock(spec=AssessmentAnalysis)

    assessment_service.assess.return_value = assessment
    analysis_agent.run.return_value = analysis

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
    )

    result = workflow.run(make_position())

    assert result.report_generator_used == (reporting_agent.last_generator_used)

    assert result.report_generation_error == (reporting_agent.last_error)


def test_assessment_workflow_propagates_fallback_reporting_status():
    reporting_agent = MagicMock()

    reporting_agent.run.return_value = MagicMock(
        spec=Report,
    )

    reporting_agent.last_generator_used = "FALLBACK"
    reporting_agent.last_error = "Fallback error"

    assessment_service = MagicMock()
    analysis_agent = MagicMock()

    assessment = MagicMock(spec=Assessment)
    analysis = MagicMock(spec=AssessmentAnalysis)

    assessment_service.assess.return_value = assessment
    analysis_agent.run.return_value = analysis

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
    )

    result = workflow.run(make_position())

    assert result.report_generator_used == (reporting_agent.last_generator_used)

    assert result.report_generation_error == (reporting_agent.last_error)


def test_assessment_workflow_propagates_terminal_reporting_failure():
    reporting_agent = MagicMock()
    reporting_agent.run.side_effect = RuntimeError("fallback report generation failed")

    assessment_service = MagicMock()
    analysis_agent = MagicMock()

    assessment = MagicMock(spec=Assessment)
    analysis = MagicMock(spec=AssessmentAnalysis)

    assessment_service.assess.return_value = assessment
    analysis_agent.run.return_value = analysis

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
    )

    with pytest.raises(
        RuntimeError,
        match="fallback report generation failed",
    ):
        workflow.run(make_position())

    assessment_service.assess.assert_called_once()
    analysis_agent.run.assert_called_once_with(assessment)
    reporting_agent.run.assert_called_once_with(analysis)
