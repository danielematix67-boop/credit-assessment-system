from unittest.mock import MagicMock

from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.models.report import Report


def make_position() -> CreditPosition:
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=0.0,
        ebitda=0.0,
        profit_loss=0.0,
        ebitda_margin=0.0,
        nfp_to_ebitda=0.0,
        interest_expense=0.0,
    )


def make_workflow(
    reporting_mode: str = "Deterministic",
    generator_used: str | None = "PRIMARY",
    error: str | None = None,
    error_category: str | None = None,
) -> AssessmentWorkflow:
    credit_case_service = MagicMock()
    analysis_agent = MagicMock()
    reporting_agent = MagicMock()

    credit_case_service.assess.return_value = MagicMock(spec=CreditAssessmentCase)
    analysis_agent.run.return_value = MagicMock(spec=AssessmentAnalysis)
    reporting_agent.run.return_value = MagicMock(spec=Report)
    reporting_agent.last_generator_used = generator_used
    reporting_agent.last_error = error
    reporting_agent.last_error_category = error_category

    return AssessmentWorkflow(
        credit_case_service=credit_case_service,
        case_analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
        reporting_mode=reporting_mode,
    )


def test_workflow_records_primary_execution_metadata():
    workflow = make_workflow(
        reporting_mode="Gemini + Fallback",
        generator_used="PRIMARY",
    )

    result = workflow.run(make_position())
    metadata = result.execution_metadata

    assert metadata is not None
    assert metadata.execution_id
    assert metadata.started_at.tzinfo is not None
    assert metadata.reporting_mode == "Gemini + Fallback"
    assert metadata.generator_used == "PRIMARY"
    assert metadata.fallback_used is False
    assert metadata.error_category is None


def test_workflow_records_fallback_execution_metadata():
    workflow = make_workflow(
        reporting_mode="Ollama + Fallback",
        generator_used="FALLBACK",
        error="Provider unavailable",
        error_category="SERVICE_UNAVAILABLE",
    )

    result = workflow.run(make_position())
    metadata = result.execution_metadata

    assert metadata is not None
    assert metadata.reporting_mode == "Ollama + Fallback"
    assert metadata.generator_used == "FALLBACK"
    assert metadata.fallback_used is True
    assert metadata.error_category == "SERVICE_UNAVAILABLE"


def test_workflow_records_non_negative_execution_timings():
    workflow = make_workflow()

    result = workflow.run(make_position())
    metadata = result.execution_metadata

    assert metadata is not None
    assert metadata.assessment_elapsed_time >= 0
    assert metadata.analysis_elapsed_time >= 0
    assert metadata.reporting_elapsed_time >= 0
    assert metadata.total_elapsed_time >= 0
    assert metadata.total_elapsed_time >= metadata.assessment_elapsed_time
    assert metadata.total_elapsed_time >= metadata.analysis_elapsed_time
    assert metadata.total_elapsed_time >= metadata.reporting_elapsed_time


def test_workflow_generates_unique_execution_ids():
    workflow = make_workflow()

    first_result = workflow.run(make_position())
    second_result = workflow.run(make_position())

    assert first_result.execution_metadata is not None
    assert second_result.execution_metadata is not None
    assert (
        first_result.execution_metadata.execution_id
        != second_result.execution_metadata.execution_id
    )
