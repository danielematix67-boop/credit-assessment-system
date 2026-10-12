import re

from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup
from src.rules.base.status import RuleStatus


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
    _THINK_BLOCK_PATTERN = re.compile(
        r"<think>.*?</think>",
        re.IGNORECASE | re.DOTALL,
    )
    _ASSESSMENT_AREA_HEADING_PATTERN = re.compile(
        r"^\s*(?:#{1,6}\s*)?"
        r"(?:\*\*)?"
        r"(?:\d+[.)]\s*)?"
        r"(Customer Profile|Financial Analysis|Behavioural Analysis|Debt Sustainability)"
        r"(?:\*\*)?"
        r"(?:\s*:\s*(?:[-–—][ \t]*)?(.*)|[ \t]*)$",
        re.IGNORECASE,
    )
    _INLINE_ASSESSMENT_AREA_PATTERN = re.compile(
        r"(?<![A-Za-z])(?:#{1,6}\s*)?(?:\*\*)?"
        r"(Customer Profile|Financial Analysis|Behavioural Analysis|Debt Sustainability)"
        r"(?:\*\*)?\s*:\s*",
        re.IGNORECASE,
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
        self._validate_triggered_evidence_coverage(
            narrative,
            analysis.rule_evidence or analysis.key_findings,
        )
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
        paragraphs = cls._extract_assessment_area_paragraphs(narrative)
        if paragraphs is None:
            detected_headings = [
                match.group(1)
                for match in cls._INLINE_ASSESSMENT_AREA_PATTERN.finditer(narrative)
            ]
            paragraph_count = sum(
                bool(part.strip()) for part in narrative.split("\n\n")
            )
            raise ValueError(
                "LLM narrative must contain exactly one paragraph for each "
                "assessment area. "
                f"Detected headings: {detected_headings or 'none'}; "
                f"blank-line paragraphs: {paragraph_count}."
            )

        return "\n\n".join(
            f"**{category}**\n\n{paragraph}"
            for category, paragraph in zip(
                cls._ASSESSMENT_AREA_ORDER,
                paragraphs,
                strict=True,
            )
        )

    @classmethod
    def _extract_assessment_area_paragraphs(
        cls,
        narrative: str,
    ) -> list[str] | None:
        """Normalize common LLM section formats into four paragraphs."""
        expected = [area.casefold() for area in cls._ASSESSMENT_AREA_ORDER]
        lines = narrative.splitlines()

        heading_matches: list[tuple[int, str, str]] = []
        for index, line in enumerate(lines):
            # Ollama may wrap labels in Markdown bold, including
            # "**Customer Profile:**". Normalize decoration before parsing.
            candidate = line.replace("**", "").strip()
            match = cls._ASSESSMENT_AREA_HEADING_PATTERN.fullmatch(candidate)
            if match:
                heading_matches.append(
                    (index, match.group(1).casefold(), (match.group(2) or "").strip())
                )

        if heading_matches:
            found = [area for _, area, _ in heading_matches]
            if len(found) == len(expected) and found == expected:
                paragraphs: list[str] = []
                for position, (line_index, _, inline_content) in enumerate(
                    heading_matches
                ):
                    end_line = (
                        heading_matches[position + 1][0]
                        if position + 1 < len(heading_matches)
                        else len(lines)
                    )
                    body_parts = [
                        line.strip()
                        for line in lines[line_index + 1 : end_line]
                        if line.strip()
                    ]
                    paragraph = " ".join(
                        part for part in [inline_content, *body_parts] if part
                    ).strip()
                    paragraph = re.sub(r"\s+", " ", paragraph)
                    if not paragraph:
                        break
                    paragraphs.append(paragraph)
                else:
                    return paragraphs

        # Some local models return all four labeled sections on one physical
        # line, or mix headings and prose without blank lines. Parse the labels
        # across the full response as a second, tolerant format.
        inline_matches = list(cls._INLINE_ASSESSMENT_AREA_PATTERN.finditer(narrative))

        # Small local models sometimes repeat each section label, e.g.
        # "Customer Profile: Customer Profile: ...". Collapse only consecutive
        # duplicate labels, preserving the required order of the four areas.
        heading_groups: list[tuple[str, re.Match[str], re.Match[str]]] = []
        for match in inline_matches:
            area = match.group(1).casefold()
            if heading_groups and heading_groups[-1][0] == area:
                previous_area, first_match, _ = heading_groups[-1]
                heading_groups[-1] = (previous_area, first_match, match)
            else:
                heading_groups.append((area, match, match))

        grouped_areas = [area for area, _, _ in heading_groups]
        if grouped_areas == expected:
            paragraphs = []
            for position, (_, _, last_match) in enumerate(heading_groups):
                # Stop at the FIRST label of the next section so its duplicate
                # label cannot leak into the current paragraph.
                end = (
                    heading_groups[position + 1][1].start()
                    if position + 1 < len(heading_groups)
                    else len(narrative)
                )
                paragraph = narrative[last_match.end() : end].strip()
                paragraph = re.sub(r"^[-–—*#\\s]+|[-–—*#\\s]+$", "", paragraph)
                paragraph = re.sub(r"\\s+", " ", paragraph).strip()
                if not paragraph:
                    return None
                paragraphs.append(paragraph)
            return paragraphs

        # The unlabeled fallback must not hide invalid labeled sections.
        # Reject incomplete, duplicated, or misordered headings explicitly.
        if heading_matches or inline_matches:
            return None

        paragraphs = [
            re.sub(r"\s+", " ", part.strip())
            for part in narrative.split("\n\n")
            if part.strip()
        ]
        if len(paragraphs) == len(expected):
            return paragraphs
        return None

    @classmethod
    def _validate_triggered_evidence_coverage(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> None:
        """
        Reject narratives that omit triggered indicators or place them in another area.

        This check is based on deterministic indicator labels, not on model-
        generated values or a second credit-risk assessment. The ReportingAgent
        uses the deterministic report if this contract fails.
        """
        paragraphs = cls._extract_assessment_area_paragraphs(narrative)
        if paragraphs is None:
            # Structural validation reports the canonical error later.
            return

        paragraph_by_area = {
            area.casefold(): paragraph
            for area, paragraph in zip(
                cls._ASSESSMENT_AREA_ORDER,
                paragraphs,
                strict=True,
            )
        }

        def normalize(value: str) -> str:
            return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

        missing: list[str] = []
        for finding in findings:
            if finding.status != RuleStatus.TRIGGERED or not finding.indicator:
                continue
            area_name = finding.assessment_area or finding.category
            paragraph = paragraph_by_area.get(area_name.casefold())

            # Coverage can only be enforced when the finding has an authoritative
            # macro-area. Legacy/lightweight analyses may use categories such as
            # "Financial Risk", "Revenue" or "Profitability"; these are not
            # equivalent to one of the four report sections.
            if paragraph is None:
                continue

            indicator = normalize(finding.indicator)
            if not indicator or indicator not in normalize(paragraph):
                missing.append(f"{area_name}: {finding.indicator}")

        if missing:
            raise ValueError(
                "LLM narrative omitted or misplaced triggered deterministic evidence: "
                + "; ".join(missing)
            )

    @classmethod
    def _extract_indicator_values(
        cls,
        findings: list[AnalysisFinding],
    ) -> list[str]:
        """Extract unique source indicators while preserving their source order."""
        values = cls._INDICATOR_PATTERN.findall(
            " ".join(finding.text for finding in findings)
        )
        return list(dict.fromkeys(values))

    @classmethod
    def _sanitize_indicator_grounding(
        cls,
        narrative: str,
        findings: list[AnalysisFinding],
    ) -> str:
        """Remove unsupported numeric claims while preserving safe qualitative text."""
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
        """Reject numeric indicators that are not grounded in deterministic findings."""
        source_values = {
            cls._normalise_indicator(value)
            for value in cls._extract_indicator_values(findings)
        }
        for value in cls._INDICATOR_PATTERN.findall(narrative):
            if cls._normalise_indicator(value) not in source_values:
                raise ValueError(f"unsupported indicator value: {value}")
        return narrative

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
        # Qwen/Ollama models may emit an internal reasoning block even when
        # explicitly instructed not to. It is not part of the executive
        # narrative and must never reach the structural parser.
        narrative = cls._THINK_BLOCK_PATTERN.sub("", narrative).strip()
        narrative = cls._STATUS_PREFIX_PATTERN.sub("", narrative, count=1).strip()
        narrative = cls._NUMERIC_SPACING_PATTERN.sub(".", narrative)
        narrative = cls._remove_category_prefixes(narrative)
        if not narrative:
            raise ValueError("LLM returned an empty narrative")
        return narrative

    @classmethod
    def _remove_category_prefixes(cls, narrative: str) -> str:
        lines = narrative.splitlines()
        normalized_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                normalized_lines.append("")
                continue

            # Preserve assessment-area labels, including labels followed by
            # prose on the same line. Removing these prefixes here prevents
            # the structural parser from detecting missing or misordered areas.
            if cls._ASSESSMENT_AREA_PREFIX_PATTERN.match(stripped):
                normalized_lines.append(stripped)
                continue

            if cls._ASSESSMENT_AREA_HEADING_PATTERN.fullmatch(stripped):
                normalized_lines.append(stripped)
                continue

            cleaned = cls._CATEGORY_PREFIX_PATTERN.sub("", stripped, count=1).strip()
            normalized_lines.append(cleaned)

        return "\n".join(normalized_lines).strip()
