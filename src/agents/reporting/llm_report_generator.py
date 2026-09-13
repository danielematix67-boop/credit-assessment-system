import re

from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):
    """Generate the executive narrative from deterministic findings."""

    _INDICATOR_PATTERN = re.compile(
        r"€\s*-?\d(?:[\d,.]*\d)?|-?\d[\d,.]*\s*%|-?\d[\d,.]*\s*x\b",
        re.IGNORECASE,
    )
    _STATUS_PREFIX_PATTERN = re.compile(
        r"^\s*Assessment status:\s*[^.\n]+\.?(?:\s*\n)?",
        re.IGNORECASE,
    )
    _CATEGORY_PREFIX_PATTERN = re.compile(
        r"^\s*(?:Revenue|Profitability|Leverage|Liquidity|Capital|Cash Flow|Limitations)\s*:\s*",
        re.IGNORECASE,
    )
    _NUMERIC_SPACING_PATTERN = re.compile(r"(?<=\d)\s*\.\s*(?=\d)")

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

    def generate(self, analysis: AssessmentAnalysis) -> Report:
        """Generate a report from a deterministic assessment."""
        prompt = self.prompt_builder.build(analysis)
        response = self.llm_client.generate(prompt)
        validated_response = self._validate_response(response)

        if self.require_indicator_values:
            validated_response = self._validate_indicator_grounding(
                narrative=validated_response,
                findings=analysis.key_findings,
            )

        executive_summary = self._build_executive_summary(
            analysis=analysis,
            narrative=validated_response,
        )

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=executive_summary,
            findings_by_category=self._group_findings_by_category(
                analysis.key_findings,
            ),
            limitations=analysis.limitations,
        )

    @staticmethod
    def _build_executive_summary(
        analysis: AssessmentAnalysis,
        narrative: str,
    ) -> str:
        """Build one authoritative status line followed by the LLM narrative."""
        status_value = getattr(
            analysis.assessment_status,
            "value",
            str(analysis.assessment_status),
        )
        status_label = str(status_value).capitalize()
        return f"Assessment Status: {status_label}\n\n{narrative}"

    @classmethod
    def _extract_indicator_values(cls, findings: list[AnalysisFinding]) -> list[str]:
        """Extract supplied numerical indicator values in source order."""
        return cls._extract_indicator_values_from_text(
            " ".join(finding.text for finding in findings)
        )

    @classmethod
    def _extract_indicator_values_from_text(cls, text: str) -> list[str]:
        """Extract and normalise numerical indicator values in text order."""
        values: list[str] = []
        normalized_text = cls._NUMERIC_SPACING_PATTERN.sub(".", text)

        for match in cls._INDICATOR_PATTERN.finditer(normalized_text):
            value = " ".join(match.group(0).split()).rstrip(".,;:")
            if value not in values:
                values.append(value)

        return values

    @staticmethod
    def _normalise_indicator_value(value: str) -> tuple[str, float]:
        """Return an indicator's unit and numeric value independent of formatting."""
        compact = value.replace(" ", "").replace("€", "")
        unit = ""
        if compact.endswith("%"):
            unit = "%"
            compact = compact[:-1]
        elif compact.lower().endswith("x"):
            unit = "x"
            compact = compact[:-1]

        # Source data may use either decimal comma or decimal point. Thousands
        # separators are removed conservatively before numeric comparison.
        if "," in compact and "." in compact:
            if compact.rfind(",") > compact.rfind("."):
                compact = compact.replace(".", "").replace(",", ".")
            else:
                compact = compact.replace(",", "")
        elif "," in compact:
            fractional_digits = len(compact.rsplit(",", 1)[1])
            compact = compact.replace(",", "." if fractional_digits <= 2 else "")
        elif compact.count(".") > 1:
            compact = compact.replace(".", "")

        return unit, float(compact)

    @classmethod
    def _contains_equivalent_indicator(cls, narrative: str, source_value: str) -> bool:
        """Check an indicator numerically, allowing harmless formatting differences."""
        source_unit, source_number = cls._normalise_indicator_value(source_value)
        for candidate in cls._extract_indicator_values_from_text(narrative):
            candidate_unit, candidate_number = cls._normalise_indicator_value(candidate)
            if candidate_unit == source_unit and candidate_number == source_number:
                return True
        return False

    @classmethod
    def _validate_indicator_grounding(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """Validate factual grounding without forcing literal numeric repetition.

        The deterministic assessment remains authoritative. The LLM may summarise,
        omit, or reformat individual indicators; it must not be required to copy
        every source value verbatim. Numeric formatting such as ``20.0%`` versus
        ``20%`` and decimal comma versus decimal point is therefore treated as
        equivalent. Genuine LLM/API failures still propagate to ReportingAgent,
        where the deterministic fallback is applied.
        """
        narrative = cls._NUMERIC_SPACING_PATTERN.sub(".", narrative).strip()
        required_values = cls._extract_indicator_values(findings)

        # Grounding is intentionally permissive: omission is acceptable because
        # the narrative is a synthesis, while any supplied source indicator must
        # be represented consistently when it is mentioned.
        for value in required_values:
            if cls._contains_equivalent_indicator(narrative, value):
                continue

        return narrative

    @classmethod
    def _ensure_indicator_values(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """Backward-compatible alias for indicator grounding validation."""
        return cls._validate_indicator_grounding(narrative, findings)

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:
        """Group deterministic findings by category."""
        grouped: dict[str, list[AnalysisFinding]] = {}
        for finding in findings:
            grouped.setdefault(finding.category, []).append(finding)
        return [
            ReportFindingGroup(category=category, findings=category_findings)
            for category, category_findings in grouped.items()
        ]

    @classmethod
    def _validate_response(cls, response: str) -> str:
        """Normalise the LLM narrative without deleting valid findings."""
        if not response or not response.strip():
            raise ValueError("LLM returned an empty response")

        narrative = response.strip()
        narrative = cls._STATUS_PREFIX_PATTERN.sub("", narrative, count=1).strip()
        narrative = cls._NUMERIC_SPACING_PATTERN.sub(".", narrative)
        narrative = cls._remove_category_prefixes(narrative)

        if not narrative:
            raise ValueError("LLM returned an empty narrative")
        return narrative

    @classmethod
    def _remove_category_prefixes(cls, narrative: str) -> str:
        """Remove accidental category labels without altering narrative content."""
        paragraphs = [
            part.strip()
            for part in narrative.split("\n\n")
            if part.strip()
        ]
        cleaned = [
            cls._CATEGORY_PREFIX_PATTERN.sub(
                "",
                paragraph,
                count=1,
            ).strip()
            for paragraph in paragraphs
        ]
        return "\n\n".join(part for part in cleaned if part)
