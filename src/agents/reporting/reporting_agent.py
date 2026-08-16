import logging

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


logger = logging.getLogger(__name__)


def _get_llm_error_message(exc: Exception) -> str:
    """
    Convert technical LLM errors into a concise,
    human-readable message.

    The reporting agent is provider-agnostic:
    the actual LLM implementation is hidden behind
    the ReportGenerator / LLMClient abstractions.
    """

    status_code = getattr(exc, "status_code", None)
    message = str(exc).lower()

    # --------------------------------------------------------
    # Rate limiting
    # --------------------------------------------------------

    if status_code == 429 or "resource_exhausted" in message:
        return "LLM resource limit exceeded."

    # --------------------------------------------------------
    # Service unavailable
    # --------------------------------------------------------

    if status_code == 503 or "service unavailable" in message:
        return "LLM service is temporarily unavailable."

    # Ollama commonly produces connection-related errors
    # when the local server is not running.
    if (
        "connection refused" in message
        or "failed to connect" in message
        or "connection error" in message
        or "connecterror" in message
    ):
        return "Local LLM service is unavailable."

    # --------------------------------------------------------
    # Authentication / permissions
    # --------------------------------------------------------

    if status_code == 401 or "unauthorized" in message:
        return "LLM authentication failed."

    if status_code == 403 or "permission denied" in message:
        return "LLM access was denied."

    # --------------------------------------------------------
    # Model not found
    # --------------------------------------------------------

    if (
        "model not found" in message
        or "model is not found" in message
        or "pull model" in message
    ):
        return "LLM model is not available."

    # --------------------------------------------------------
    # Timeout
    # --------------------------------------------------------

    if "timeout" in message or "timed out" in message:
        return "LLM request timed out."

    # --------------------------------------------------------
    # Generic error
    # --------------------------------------------------------

    return "LLM report generation failed."


class ReportingAgent(Agent[AssessmentAnalysis, Report]):

    def __init__(
        self,
        report_generator: ReportGenerator,
        fallback_generator: ReportGenerator | None = None,
    ):
        self.report_generator = report_generator
        self.fallback_generator = fallback_generator

        self.last_generator_used: str | None = None
        self.last_error: str | None = None

    def run(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        # Reset diagnostics for every execution.
        self.last_generator_used = None
        self.last_error = None

        # ====================================================
        # Primary generator
        # ====================================================

        try:
            report = self.report_generator.generate(analysis)

            self.last_generator_used = "PRIMARY"

            generator_name = type(
                self.report_generator
            ).__name__

            print(
                f"\n  [PRIMARY] Report generated successfully "
                f"({generator_name})."
            )

            return report

        # ====================================================
        # Primary failure
        # ====================================================

        except Exception as exc:

            error_message = _get_llm_error_message(exc)

            self.last_error = error_message

            logger.warning(
                "Primary report generator failed: %s",
                error_message,
            )

            # ------------------------------------------------
            # No fallback configured
            # ------------------------------------------------

            if self.fallback_generator is None:
                raise

            # ------------------------------------------------
            # Deterministic fallback
            # ------------------------------------------------

            self.last_generator_used = "FALLBACK"

            print("\n  [WARN] LLM REPORT GENERATION")
            print("  " + "-" * 50)
            print(f"  {error_message}")
            print(
                "  Using deterministic fallback report generator."
            )

            try:
                report = self.fallback_generator.generate(
                    analysis
                )

            except Exception:
                logger.exception(
                    "Deterministic fallback report generation failed."
                )

                self.last_generator_used = None

                raise

            print(
                "  [FALLBACK] Report generated successfully."
            )

            return report