import re

from src.agents.reporting.deterministic_report_generator import DeterministicReportGenerator
from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):
    """Generate the executive narrative from deterministic findings."""

    _INDICATOR_PATTERNS = (
        re.compile(r"€\s*-?\d(?:[\d,.]*\d)?"),
        re.compile(r"-?\d[\d,.]*\s*%"),
        re.compile(r"-?\d[\d,.]*\s*x\b", re.IGNORECASE),
    )
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
    _SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?]+")

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
            try:
                validated_response = self._validate_indicator_grounding(
                    narrative=validated_response,
                    findings=analysis.key_findings,
                )
            except ValueError:
                return DeterministicReportGenerator().generate(analysis)

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

    # ============================================================
    # Indicator grounding
    # ============================================================

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

    @classmethod
    def _validate_indicator_grounding(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """Accept the LLM narrative only when every supplied indicator is present exactly once."""
        narrative = cls._NUMERIC_SPACING_PATTERN.sub(".", narrative)
        required_values = cls._extract_indicator_values(findings)

        for value in required_values:
            occurrences = narrative.count(value)
            if occurrences != 1:
                raise ValueError(
                    f"LLM narrative must contain indicator {value!r} exactly once; "
                    f"found {occurrences} occurrences"
                )

        return narrative

    @classmethod
    def _ensure_indicator_values(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """Backward-compatible alias for strict indicator validation."""
        return cls._validate_indicator_grounding(narrative, findings)

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
            grouped.setdefault(finding.category, []).append(finding)
        return [
            ReportFindingGroup(category=category, findings=category_findings)
            for category, category_findings in grouped.items()
        ]

    # ============================================================
    # LLM response validation
    # ============================================================

    @classmethod
    def _validate_response(cls, response: str) -> str:
        """Normalise the LLM narrative and remove prohibited duplication."""
        if not response or not response.strip():
            raise ValueError("LLM returned an empty response")

        narrative = response.strip()
        narrative = cls._STATUS_PREFIX_PATTERN.sub("", narrative, count=1).strip()
        narrative = cls._NUMERIC_SPACING_PATTERN.sub(".", narrative)
        narrative = cls._remove_category_prefixes(narrative)
        narrative = cls._remove_duplicate_sentences(narrative)
        narrative = cls._remove_repeated_indicator_mentions(narrative)

        if not narrative:
            raise ValueError("LLM returned an empty narrative")
        return narrative

    @classmethod
    def _remove_category_prefixes(cls, narrative: str) -> str:
        """Remove accidental category labels from the beginning of narrative paragraphs."""
        paragraphs = [part.strip() for part in narrative.split("\n\n") if part.strip()]
        cleaned = [cls._CATEGORY_PREFIX_PATTERN.sub("", paragraph, count=1).strip() for paragraph in paragraphs]
        return "\n\n".join(part for part in cleaned if part)

    @classmethod
    def _remove_duplicate_sentences(cls, narrative: str) -> str:
        """Remove exact repeated sentences while preserving paragraphs and order."""
        paragraphs = [part.strip() for part in narrative.split("\n\n") if part.strip()]
        cleaned_paragraphs: list[str] = []
        seen: set[str] = set()

        for paragraph in paragraphs:
            sentences = cls._SENTENCE_PATTERN.findall(paragraph)
            if not sentences:
                key = " ".join(paragraph.split()).casefold()
                if key not in seen:
                    seen.add(key)
                    cleaned_paragraphs.append(paragraph)
                continue

            unique_sentences: list[str] = []
            for sentence in sentences:
                cleaned = " ".join(sentence.split()).strip()
                key = cleaned.casefold()
                if key in seen:
                    continue
                seen.add(key)
                unique_sentences.append(cleaned)

            remainder = paragraph
            for sentence in sentences:
                remainder = remainder.replace(sentence, "", 1)
            remainder = " ".join(remainder.split()).strip()
            if remainder:
                unique_sentences.append(remainder)

            if unique_sentences:
                cleaned_paragraphs.append(" ".join(unique_sentences).strip())

        return "\n\n".join(cleaned_paragraphs).strip()

    @classmethod
    def _remove_repeated_indicator_mentions(cls, narrative: str) -> str:
        """Remove sentences whose indicator values have all appeared already."""
        paragraphs = [part.strip() for part in narrative.split("\n\n") if part.strip()]
        cleaned_paragraphs: list[str] = []
        seen_values: set[str] = set()

        for paragraph in paragraphs:
            kept: list[str] = []
            sentences = cls._SENTENCE_PATTERN.findall(paragraph)

            for sentence in sentences:
                values = cls._extract_indicator_values_from_text(sentence)
                if values and all(value in seen_values for value in values):
                    continue
                kept.append(" ".join(sentence.split()).strip())
                seen_values.update(values)

            if kept:
                cleaned_paragraphs.append(" ".join(kept).strip())
            elif not sentences:
                cleaned_paragraphs.append(paragraph)

        return "\n\n".join(cleaned_paragraphs).strip()
