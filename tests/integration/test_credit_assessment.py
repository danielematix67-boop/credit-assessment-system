from src.agents.workflow.workflow_factory import create_default_assessment_workflow
from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.orchestration.orchestrator_factory import (
    create_default_orchestrator,
)

from src.agents.reporting.llm_report_generator import LLMReportGenerator

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

    # The orchestrator returns the final Report.
    assert result.position_id == "POS001"
    assert result.assessment_status == AssessmentStatus.CRITICAL

    # A critical assessment must produce a non-empty executive summary.
    assert result.executive_summary

    # A critical assessment must contain findings.
    assert result.findings

    # Limitations may be empty when all required indicators are evaluable.
    assert isinstance(result.limitations, list)

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