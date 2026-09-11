from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus


class SyntheticLLMError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class FailingGenerator:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def generate(self, analysis: AssessmentAnalysis) -> None:
        raise self.error


ERROR_CASES = [
    (SyntheticLLMError("resource_exhausted"), "RATE_LIMIT"),
    (
        SyntheticLLMError("service unavailable", status_code=503),
        "SERVICE_UNAVAILABLE",
    ),
    (SyntheticLLMError("connection refused"), "CONNECTION_ERROR"),
    (SyntheticLLMError("unauthorized", status_code=401), "AUTHENTICATION"),
    (SyntheticLLMError("permission denied", status_code=403), "AUTHORIZATION"),
    (SyntheticLLMError("model not found"), "MODEL_UNAVAILABLE"),
    (SyntheticLLMError("request timed out"), "TIMEOUT"),
    (SyntheticLLMError("unexpected provider failure"), "GENERATION_ERROR"),
]


def _analysis() -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id="ERROR-FALLBACK-001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )


def test_llm_error_categories_trigger_deterministic_fallback() -> None:
    for error, expected_category in ERROR_CASES:
        analysis = _analysis()
        agent = ReportingAgent(
            report_generator=FailingGenerator(error),
            fallback_generator=DeterministicReportGenerator(),
        )

        report = agent.run(analysis)

        assert agent.last_generator_used == "FALLBACK"
        assert agent.last_error_category == expected_category
        assert report.position_id == analysis.position_id
        assert report.assessment_status is analysis.assessment_status
        assert report.limitations is analysis.limitations
