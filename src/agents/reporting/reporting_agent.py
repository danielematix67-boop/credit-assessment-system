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

    The original exception message is preserved when
    no specific error category can be identified.
    """

    status_code = getattr(exc, "status_code", None)
    message = str(exc).strip()
    normalized_message = message.lower()

    # ========================================================
    # Rate limiting
    # ========================================================

    if status_code == 429 or "resource_exhausted" in normalized_message:
        return "LLM resource limit exceeded."

    # ========================================================
    # Service unavailable
    # ========================================================

    if status_code == 503 or "service unavailable" in normalized_message:
        return "LLM service is temporarily unavailable."

    # ========================================================
    # Connection errors
    # ========================================================

    if (
        "connection refused" in normalized_message
        or "failed to connect" in normalized_message
        or "connection error" in normalized_message
        or "connecterror" in normalized_message
        or "connectionreseterror" in normalized_message
        or "connection aborted" in normalized_message
    ):
        return "Local LLM service is unavailable."

    # ========================================================
    # Authentication / permissions
    # ========================================================

    if status_code == 401 or "unauthorized" in normalized_message:
        return "LLM authentication failed."

    if status_code == 403 or "permission denied" in normalized_message:
        return "LLM access was denied."

    # ========================================================
    # Model not found
    # ========================================================

    if (
        "model not found" in normalized_message
        or "model is not found" in normalized_message
        or "pull model" in normalized_message
    ):
        return "LLM model is not available."

    # ========================================================
    # Timeout
    # ========================================================

    if "timeout" in normalized_message or "timed out" in normalized_message:
        return "LLM request timed out."

    # ========================================================
    # Generic error
    # ========================================================

    if message:
        return f"LLM report generation failed: {message}"

    return "LLM report generation failed."


class ReportingAgent(Agent[AssessmentAnalysis, Report]):
    def __init__(
        self,
        report_generator: ReportGenerator,
        fallback_generator: ReportGenerator | None = None,
    ) -> None:
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

            generator_name = type(self.report_generator).__name__

            print(f"\n  [PRIMARY] Report generated successfully ({generator_name}).")

            return report

        # ====================================================
        # Primary failure
        # ====================================================

        except Exception as exc:
            error_message = _get_llm_error_message(exc)

            self.last_error = error_message

            generator_name = type(self.report_generator).__name__

            logger.warning(
                "Primary report generator failed (%s): %s",
                generator_name,
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

            print("\n  [WARN] PRIMARY REPORT GENERATION")
            print("  " + "-" * 50)
            print(f"  Generator: {generator_name}")
            print(f"  Reason: {error_message}")
            print("  Action: Using deterministic fallback report generator.")

            try:
                report = self.fallback_generator.generate(analysis)

            except Exception:
                logger.exception("Deterministic fallback report generation failed.")

                self.last_generator_used = None

                raise

            print("  [FALLBACK] Report generated successfully.")

            return report
