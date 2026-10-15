import logging
import re
from dataclasses import replace
from datetime import datetime

from src.agents.base.agent import Agent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report
from src.rules.base.status import RuleStatus

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

    @staticmethod
    def _add_customer_profile_context(
        report: Report,
        analysis: AssessmentAnalysis,
    ) -> Report:
        """Replace generated Customer Profile prose with the fixed deterministic block."""
        profile = analysis.customer_profile
        if profile is None:
            return report

        profile_text = DeterministicReportGenerator._render_customer_profile_context(
            profile.sections()
        )
        if not profile_text:
            return report

        summary = report.executive_summary
        customer_heading = re.compile(
            r"(?m)^(?:###\s*|\*\*)Customer Profile(?:\*\*)?\s*$",
            re.IGNORECASE,
        )
        next_heading = re.compile(
            r"(?m)^(?:###\s*|\*\*)"
            r"(?:Financial Analysis|Behavioural Analysis|Debt Sustainability)"
            r"(?:\*\*)?\s*$",
            re.IGNORECASE,
        )
        match = customer_heading.search(summary)
        if match is None:
            logger.warning(
                "Could not locate Customer Profile heading to insert fixed context."
            )
            return report

        following = next_heading.search(summary, match.end())
        if following is None:
            logger.warning(
                "Could not locate the next assessment heading after Customer Profile."
            )
            return report

        evidence = analysis.rule_evidence or analysis.key_findings
        triggered = [
            finding
            for finding in evidence
            if finding.status == RuleStatus.TRIGGERED
            and (finding.assessment_area or finding.category).casefold()
            == "customer profile"
        ]
        rule_sentences = [
            finding.text.rstrip(".") + "."
            for finding in triggered
            if finding.text.strip()
        ]

        block = profile_text
        if rule_sentences:
            block += (
                "\n\n**Deterministic rule findings**\n\n"
                + " ".join(rule_sentences)
            )

        updated_summary = (
            summary[: match.end()]
            + "\n\n"
            + block
            + "\n\n"
            + summary[following.start() :]
        )
        return replace(report, executive_summary=updated_summary)

    @staticmethod
    def _add_behavioural_context(
        report: Report,
        analysis: AssessmentAnalysis,
    ) -> Report:
        """Prefix the CR exposure summary independently of the selected generator."""
        context = analysis.behavioural_context
        required = (
            "cr_reference_date",
            "total_utilized_system",
            "utilized_term",
            "utilized_revocable",
            "utilized_self_liquidating",
        )
        if any(context.get(key) in (None, "") for key in required):
            return report

        try:
            reference_date = datetime.strptime(
                str(context["cr_reference_date"]), "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
            amounts: dict[str, float] = {}
            for key in required[1:]:
                value = context[key]
                if isinstance(value, bool) or not isinstance(
                    value, (int, float, str)
                ):
                    raise TypeError(f"Invalid numeric CR context value for {key}.")
                amounts[key] = float(value)
        except (TypeError, ValueError, OverflowError):
            logger.warning("Skipping malformed CR context in executive narrative.")
            return report

        def euro(value: float) -> str:
            return f"€{value:,.0f}"

        sentence = (
            f"As of {reference_date}, total system-wide utilised exposure amounted "
            f"to approximately {euro(amounts['total_utilized_system'])}, comprising "
            f"{euro(amounts['utilized_term'])} in term facilities, "
            f"{euro(amounts['utilized_revocable'])} in revocable facilities and "
            f"{euro(amounts['utilized_self_liquidating'])} in self-liquidating facilities."
        )
        heading = re.compile(
            r"(?m)^(?:###\s*Behavioural Analysis|\*\*Behavioural Analysis\*\*)\s*$",
            re.IGNORECASE,
        )
        match = heading.search(report.executive_summary)
        if match is None:
            logger.warning(
                "Could not locate Behavioural Analysis heading to insert CR context."
            )
            return report

        insertion_point = match.end()
        summary = report.executive_summary
        separator_end = insertion_point
        while separator_end < len(summary) and summary[separator_end] in "\r\n":
            separator_end += 1
        updated_summary = (
            summary[:separator_end]
            + sentence
            + (" " if summary[separator_end:].strip() else "")
            + summary[separator_end:].lstrip()
        )
        return replace(report, executive_summary=updated_summary)

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

            return self._add_behavioural_context(
                self._add_customer_profile_context(report, analysis), analysis
            )

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

            return self._add_behavioural_context(
                self._add_customer_profile_context(report, analysis), analysis
            )
