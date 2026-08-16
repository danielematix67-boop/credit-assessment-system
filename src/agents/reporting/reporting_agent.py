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

        # Runtime diagnostics for observability.
        self.last_generator_used: str | None = None
        self.last_error: str | None = None

    def run(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        # Reset runtime diagnostics for every execution.
        self.last_generator_used = None
        self.last_error = None

        try:
            report = self.report_generator.generate(analysis)

            self.last_generator_used = "PRIMARY"

            generator_name = type(self.report_generator).__name__

            print(
                f"\n  [PRIMARY] Report generated successfully "
                f"({generator_name})."
            )

            return report

        except Exception as exc:

            if self.fallback_generator is None:
                raise

            error_message = _get_llm_error_message(exc)

            self.last_error = error_message
            self.last_generator_used = "FALLBACK"

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