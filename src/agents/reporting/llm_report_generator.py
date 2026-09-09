import re

from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):
    """
    Report generator based on an abstract LLM client.

    The LLM is used exclusively to generate the executive narrative.

    The deterministic assessment remains the source of truth for:

    - assessment status;
    - findings;
    - finding severity;
    - finding categories;
    - limitations.

    The LLM does not perform assessment logic and does not modify
    any deterministic assessment information.
    """

    _INDICATOR_PATTERNS = (
        re.compile(r"€\s*-?\d[\d,.]*"),
        re.compile(r"-?\d[\d,.]*\s*%"),
        re.compile(r"-?\d[\d,.]*\s*x\b", re.IGNORECASE),
    )

    _STATUS_PREFIX_PATTERN = re.compile(
        r"^\s*Assessment status:\s*[^.\n]+\.?(?:\s*\n)?",
        re.IGNORECASE,
    )

    _STATUS_DESCRIPTIONS = {
        AssessmentStatus.NORMAL: (
            "No significant credit-risk factors identified"
        ),
        AssessmentStatus.ATTENTION: (
            "Credit-risk factors requiring monitoring identified"
        ),
        AssessmentStatus.CRITICAL: (
            "Significant credit-risk factors affecting the credit profile identified"
        ),
    }

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: ReportPromptBuilder | None = None,
        require_indicator_values: bool = False,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = (
            prompt_builder if prompt_builder is not None else ReportPromptBuilder()
        )
        self.require_indicator_values = require_indicator_values

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        """Generate a report from a deterministic assessment."""
        prompt = self.prompt_builder.build(analysis)
        response = self.llm_client.generate(prompt)

        validated_response = self._validate_response(response)

        if self.require_indicator_values:
            validated_response = self._ensure_indicator_values(
                narrative=validated_response,
                findings=analysis.key_findings,
            )

        executive_summary = self._build_executive_summary(
            analysis=analysis,
            narrative=validated_response,
        )

        findings_by_category = self._group_findings_by_category(
            analysis.key_findings,
        )

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=executive_summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    # ============================================================
    # Executive summary
    # ============================================================

    @classmethod
    def _build_executive_summary(
        cls,
        analysis: AssessmentAnalysis,
        narrative: str,
    ) -> str:
        """Build a deterministic status line followed by the narrative."""
        status = analysis.assessment_status
        description = cls._STATUS_DESCRIPTIONS.get(
            status,
            "Assessment status could not be determined",
        )
        status_value = getattr(status, "value", str(status))

        return f"Assessment status: {status_value} — {description}.\n{narrative}"

    # ============================================================
    # Indicator grounding
    # ============================================================

    @classmethod
    def _extract_indicator_values(cls, findings: list[AnalysisFinding]) -> list[str]:
        """Extract supplied numerical indicator values from deterministic findings."""
        values: list[str] = []

        for finding in findings:
            for pattern in cls._INDICATOR_PATTERNS:
                for match in pattern.findall(finding.text):
                    normalized = " ".join(match.split())
                    if normalized not in values:
                        values.append(normalized)

        return values

    @classmethod
    def _ensure_indicator_values(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """
        Ensure local-LLM narratives retain deterministic indicator values.

        Only values absent from the generated narrative are supplemented.
        The supplement is grounded directly in the deterministic findings.
        """
        missing_values = [
            value
            for value in cls._extract_indicator_values(findings)
            if value not in narrative
        ]

        if not missing_values:
            return narrative

        missing_findings = [
            finding
            for finding in findings
            if any(value in finding.text for value in missing_values)
        ]

        grounded_findings = []
        for finding in missing_findings:
            if finding.text not in grounded_findings:
                grounded_findings.append(finding.text)

        if grounded_findings:
            supplement = "The assessment also reflects: " + "; ".join(
                grounded_findings
            )
        else:
            supplement = "The assessment also reflects indicator values: " + ", ".join(
                missing_values
            )

        return f"{narrative.rstrip()} {supplement}."

    # ============================================================
    # Finding grouping
    # ============================================================

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:
        """Group deterministic findings by category."""
        grouped: dict[str, list[AnalysisFinding]] = {}

        for finding in findings:
            grouped.setdefault(
                finding.category,
                [],
            ).append(finding)

        return [
            ReportFindingGroup(
                category=category,
                findings=category_findings,
            )
            for category, category_findings in grouped.items()
        ]

    # ============================================================
    # LLM response validation
    # ============================================================

    @classmethod
    def _validate_response(cls, response: str) -> str:
        """
        Validate and normalise the LLM-generated executive narrative.

        The assessment status is owned by the deterministic engine, so a
        status line produced by the LLM is removed before the application
        adds its authoritative status line.
        """
        if not response or not response.strip():
            raise ValueError("LLM returned an empty response")

        narrative = response.strip()
        narrative = cls._STATUS_PREFIX_PATTERN.sub("", narrative, count=1).strip()

        if not narrative:
            raise ValueError("LLM returned an empty narrative")

        return narrative
