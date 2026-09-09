import re

from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):
    """Generate the executive narrative from deterministic findings."""

    _INDICATOR_PATTERNS = (
        re.compile(r"€\s*-?\d(?:[\d,.]*\d)?"),
        re.compile(r"-?\d[\d,.]*\s*%"),
        re.compile(r"-?\d[\d,.]*\s*x\b", re.IGNORECASE),
    )

    _STATUS_PREFIX_PATTERN = re.compile(
        r"^\s*Assessment status:\s*[^.\n]+\.?(?:\s*\n)?",
        re.IGNORECASE,
    )

    _NUMERIC_SPACING_PATTERN = re.compile(r"(?<=\d)\s+\.\s*(?=\d)")
    _SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?]+")

    _STATUS_DESCRIPTIONS = {
        AssessmentStatus.NORMAL: "No significant credit-risk factors identified",
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

    def generate(self, analysis: AssessmentAnalysis) -> Report:
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

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=executive_summary,
            findings_by_category=self._group_findings_by_category(
                analysis.key_findings,
            ),
            limitations=analysis.limitations,
        )

    @classmethod
    def _build_executive_summary(
        cls,
        analysis: AssessmentAnalysis,
        narrative: str,
    ) -> str:
        """Build one authoritative status line followed by the narrative."""
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
        """Extract supplied numerical indicator values from findings."""
        values: list[str] = []
        for finding in findings:
            for pattern in cls._INDICATOR_PATTERNS:
                for match in pattern.findall(finding.text):
                    normalized = " ".join(match.split()).rstrip(".,;:")
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
        Ensure local-LLM narratives retain every deterministic indicator value.

        Missing values are inserted into the paragraph corresponding to their
        deterministic category. If the LLM still omits a value, the output is
        rejected so the reporting layer can use its deterministic fallback
        rather than append an artificial list of values to the report.
        """
        required_values = cls._extract_indicator_values(findings)
        missing_values = [value for value in required_values if value not in narrative]
        if not missing_values:
            return narrative

        paragraphs = [part.strip() for part in narrative.split("\n\n") if part.strip()]
        if not paragraphs:
            paragraphs = [narrative.strip()]

        for finding in findings:
            relevant_missing = [
                value for value in missing_values if value in finding.text
            ]
            if not relevant_missing:
                continue

            label = cls._indicator_label(finding.text, relevant_missing[0])
            sentence = f"{label}: {', '.join(relevant_missing)}."
            target_index = cls._category_index_for_finding(finding, findings)

            while len(paragraphs) <= target_index:
                paragraphs.append("")

            if paragraphs[target_index]:
                paragraphs[target_index] = (
                    f"{paragraphs[target_index].rstrip('. ')}. {sentence}"
                )
            else:
                paragraphs[target_index] = sentence

            for value in relevant_missing:
                if value in missing_values:
                    missing_values.remove(value)

        if missing_values:
            raise ValueError(
                "LLM narrative omitted required indicator values: "
                + ", ".join(missing_values)
            )

        return "\n\n".join(paragraphs)

    @staticmethod
    def _category_index_for_finding(
        finding: AnalysisFinding,
        findings: list[AnalysisFinding],
    ) -> int:
        """Return the deterministic category position of a finding."""
        categories: list[str] = []
        for item in findings:
            if item.category not in categories:
                categories.append(item.category)
        return categories.index(finding.category)

    @staticmethod
    def _indicator_label(text: str, value: str) -> str:
        """Derive a concise indicator label from a deterministic finding."""
        prefix = text.split(value, 1)[0].strip(" ,:;.-")
        prefix = re.sub(
            r"\b(?:declined|increased|decreased|stands|is|was|remains|reached|at|to)\b.*$",
            "",
            prefix,
            flags=re.IGNORECASE,
        ).strip(" ,:;.-")
        return prefix or "Indicator value"

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
        narrative = cls._remove_duplicate_sentences(narrative)
        narrative = cls._remove_repeated_indicator_mentions(narrative)

        if not narrative:
            raise ValueError("LLM returned an empty narrative")
        return narrative

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
        """Keep the first sentence containing each indicator value only."""
        paragraphs = [part.strip() for part in narrative.split("\n\n") if part.strip()]
        cleaned_paragraphs: list[str] = []
        seen_values: set[str] = set()

        for paragraph in paragraphs:
            kept: list[str] = []
            for sentence in cls._SENTENCE_PATTERN.findall(paragraph):
                values = cls._extract_indicator_values(
                    [
                        AnalysisFinding(
                            rule_id="_validation",
                            category="_validation",
                            severity=None,  # type: ignore[arg-type]
                            text=sentence,
                        )
                    ]
                )
                repeated = values and all(value in seen_values for value in values)
                if repeated:
                    continue
                kept.append(" ".join(sentence.split()).strip())
                seen_values.update(values)

            if kept:
                cleaned_paragraphs.append(" ".join(kept).strip())
            elif not cls._SENTENCE_PATTERN.findall(paragraph):
                cleaned_paragraphs.append(paragraph)

        return "\n\n".join(cleaned_paragraphs).strip()
