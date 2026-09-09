import logging

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report

logger = logging.getLogger(__name__)


def _get_llm_error_details(exc: Exception) -> tuple[str, str]:
    """Return a stable error category and concise human-readable message."""
    status_code = getattr(exc, "status_code", None)
    message = str(exc).strip()
    normalized_message = message.lower()

    if status_code == 429 or "resource_exhausted" in normalized_message:
        return "RATE_LIMIT", "LLM resource limit exceeded."

    if status_code == 503 or "service unavailable" in normalized_message:
        return "SERVICE_UNAVAILABLE", "LLM service is temporarily unavailable."

    if (
        "connection refused" in normalized_message
        or "failed to connect" in normalized_message
        or "connection error" in normalized_message
        or "connecterror" in normalized_message
        or "connectionreseterror" in normalized_message
        or "connection aborted" in normalized_message
    ):
        return "CONNECTION_ERROR", "Local LLM service is unavailable."

    if status_code == 401 or "unauthorized" in normalized_message:
        return "AUTHENTICATION", "LLM authentication failed."

    if status_code == 403 or "permission denied" in normalized_message:
        return "AUTHORIZATION", "LLM access was denied."

    if (
        "model not found" in normalized_message
        or "model is not found" in normalized_message
        or "pull model" in normalized_message
    ):
        return "MODEL_UNAVAILABLE", "LLM model is not available."

    if "timeout" in normalized_message or "timed out" in normalized_message:
        return "TIMEOUT", "LLM request timed out."

    if message:
        return "GENERATION_ERROR", f"LLM report generation failed: {message}"

    return "GENERATION_ERROR", "LLM report generation failed."


def _get_llm_error_message(exc: Exception) -> str:
    """Convert a technical LLM error into a concise human-readable message."""
    return _get_llm_error_details(exc)[1]


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
        self.last_error_category: str | None = None

    def run(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        # Reset diagnostics for every execution.
        self.last_generator_used = None
        self.last_error = None
        self.last_error_category = None

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
            error_category, error_message = _get_llm_error_details(exc)

            self.last_error = error_message
            self.last_error_category = error_category

            generator_name = type(self.report_generator).__name__

            logger.warning(
                "Primary report generator failed (%s): %s",
                generator_name,
                error_message,
            )

            if self.fallback_generator is None:
                raise

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
