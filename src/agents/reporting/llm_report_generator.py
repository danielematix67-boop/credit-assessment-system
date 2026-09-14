import re

from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):
    """Generate qualitative executive narrative from deterministic findings."""

    _INDICATOR_PATTERN = re.compile(
        r"€\s*-?\d(?:[\d,.]*\d)?|-?\d[\d,.]*\s*%|-?\d[\d,.]*\s*x\b",
        re.IGNORECASE,
    )
    _STATUS_PREFIX_PATTERN = re.compile(
        r"^\s*Assessment status:\s*[^.\n]+\.?(?:\s*\n)?", re.IGNORECASE
    )
    _CATEGORY_PREFIX_PATTERN = re.compile(
        r"^\s*(?:Revenue|Profitability|Leverage|Liquidity|Capital|Cash Flow|Limitations)\s*:\s*",
        re.IGNORECASE,
    )
    _ASSESSMENT_AREA_PREFIX_PATTERN = re.compile(
        r"^\s*(?:Customer Profile|Financial Analysis|Behavioural Analysis|Debt Sustainability)\s*:\s*",
        re.IGNORECASE,
    )
    _NUMERIC_SPACING_PATTERN = re.compile(r"(?<=\d)\s*\.\s*(?=\d)")
    _SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
    _ASSESSMENT_AREA_ORDER = (
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    )

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
        response = self.llm_client.generate(self.prompt_builder.build(analysis))
        narrative = self._validate_response(response)
        if self.require_indicator_values:
            narrative = self._sanitize_indicator_grounding(
                narrative,
                analysis.key_findings,
            )
        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=self._build_executive_summary(analysis, narrative),
            findings_by_category=self._group_findings_by_category(analysis.key_findings),
            limitations=analysis.limitations,
        )

    @classmethod
    def _build_executive_summary(
        cls,
        analysis: AssessmentAnalysis,
        narrative: str,
    ) -> str:
        status_value = getattr(
            analysis.assessment_status,
            "value",
            str(analysis.assessment_status),
        )
        sections = cls._format_assessment_area_sections(analysis, narrative)
        return f"Assessment Status: {str(status_value).capitalize()}\n\n{sections}"

    @classmethod
    def _format_assessment_area_sections(
        cls,
        analysis: AssessmentAnalysis,
        narrative: str,
    ) -> str:
        findings = analysis.rule_evidence or analysis.key_findings
        categories = cls._ordered_assessment_areas(findings)
        if not categories:
            return narrative
        paragraphs = [
            part.strip() for part in narrative.split("\n\n") if part.strip()
        ]
        if len(paragraphs) != len(categories):
            raise ValueError(
                "LLM narrative must contain exactly one paragraph per represented "
                "assessment area."
            )
        return "\n\n".join(
            f"**{category}**\n\n{paragraph}"
            for category, paragraph in zip(categories, paragraphs, strict=True)
        )

    @classmethod
    def _ordered_assessment_areas(
        cls,
        findings: list[AnalysisFinding],
    ) -> list[str]:
        represented = {
            (finding.assessment_area or finding.category).casefold()
            for finding in findings
        }
        return [
            area
            for area in cls._ASSESSMENT_AREA_ORDER
            if area.casefold() in represented
        ]

    @classmethod
    def _extract_indicator_values(
        cls,
        findings: list[AnalysisFinding],
    ) -> list[str]:
        return cls._INDICATOR_PATTERN.findall(
            " ".join(finding.text for finding in findings)
        )

    @classmethod
    def _sanitize_indicator_grounding(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """Keep numeric rendering deterministic without activating fallback."""
        source_values = {
            cls._normalise_indicator(value)
            for value in cls._extract_indicator_values(findings)
        }
        paragraphs = [
            part.strip() for part in narrative.split("\n\n") if part.strip()
        ]
        sanitized_paragraphs: list[str] = []
        for paragraph in paragraphs:
            sentences = [
                sentence.strip()
                for sentence in cls._SENTENCE_PATTERN.split(paragraph)
                if sentence.strip()
            ]
            safe_sentences: list[str] = []
            for sentence in sentences:
                values = cls._INDICATOR_PATTERN.findall(sentence)
                if not values or all(
                    cls._normalise_indicator(value) in source_values
                    for value in values
                ):
                    safe_sentences.append(sentence)
            sanitized_paragraphs.append(
                " ".join(safe_sentences).strip()
                or "The assessment findings are summarised below."
            )
        return "\n\n".join(sanitized_paragraphs)

    @staticmethod
    def _normalise_indicator(value: str) -> tuple[str, float]:
        compact = value.replace(" ", "").replace("€", "")
        unit = ""
        if compact.endswith("%"):
            unit, compact = "%", compact[:-1]
        elif compact.lower().endswith("x"):
            unit, compact = "x", compact[:-1]
        if "," in compact and "." in compact:
            if compact.rfind(",") > compact.rfind("."):
                compact = compact.replace(".", "").replace(",", ".")
            else:
                compact = compact.replace(",", "")
        elif "," in compact:
            digits = len(compact.rsplit(",", 1)[1])
            compact = compact.replace(",", "." if digits <= 2 else "")
        return unit, float(compact)

    @classmethod
    def _validate_indicator_grounding(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        return cls._sanitize_indicator_grounding(narrative, findings)

    @classmethod
    def _ensure_indicator_values(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        return cls._sanitize_indicator_grounding(narrative, findings)

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:
        grouped: dict[str, list[AnalysisFinding]] = {}
        for finding in findings:
            grouped.setdefault(finding.category, []).append(finding)
        return [
            ReportFindingGroup(category=category, findings=items)
            for category, items in grouped.items()
        ]

    @classmethod
    def _validate_response(cls, response: str) -> str:
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
        paragraphs = [
            part.strip() for part in narrative.split("\n\n") if part.strip()
        ]
        return "\n\n".join(
            cls._ASSESSMENT_AREA_PREFIX_PATTERN.sub(
                "",
                cls._CATEGORY_PREFIX_PATTERN.sub("", paragraph, count=1).strip(),
                count=1,
            ).strip()
            for paragraph in paragraphs
        )
