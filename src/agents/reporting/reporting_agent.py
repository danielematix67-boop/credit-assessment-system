import logging

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


logger = logging.getLogger(__name__)


def _get_llm_error_message(exc: Exception) -> str:
    """
    Convert technical LLM/API errors into a concise,
    human-readable message.
    """

    status_code = getattr(exc, "status_code", None)
    message = str(exc).lower()

    if status_code == 429 or "resource_exhausted" in message:
        return "Gemini API quota exceeded."

    if status_code == 503 or "unavailable" in message:
        return "Gemini service is temporarily unavailable."

    if status_code == 401 or "unauthorized" in message:
        return "Gemini API authentication failed."

    if status_code == 403 or "permission" in message:
        return "Gemini API access was denied."

    if "timeout" in message:
        return "Gemini request timed out."

    return "LLM report generation failed."


class ReportingAgent(Agent[AssessmentAnalysis, Report]):

    def __init__(
        self,
        report_generator: ReportGenerator,
        fallback_generator: ReportGenerator | None = None,
    ):
        self.report_generator = report_generator
        self.fallback_generator = fallback_generator

    def run(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        try:
            report = self.report_generator.generate(analysis)

            print(
                "\n  [LLM] Report generated successfully."
            )

            return report

        except Exception as exc:

            if self.fallback_generator is None:
                raise

            error_message = _get_llm_error_message(exc)

            logger.warning(
                "Primary report generator failed: %s",
                error_message,
            )

            print("\n  [WARN] LLM REPORT GENERATION")
            print("  " + "-" * 50)
            print(f"  {error_message}")
            print(
                "  Using deterministic fallback report generator."
            )

            report = self.fallback_generator.generate(analysis)

            print(
                "  [FALLBACK] Report generated successfully."
            )

            return report
