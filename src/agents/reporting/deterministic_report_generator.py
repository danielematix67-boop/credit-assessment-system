from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup
from src.rules.base.status import RuleStatus


class DeterministicReportGenerator(ReportGenerator):
    _ASSESSMENT_AREA_ORDER = (
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    )

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        self._validate_rule_evidence(analysis.key_findings)
        summary = self._generate_summary(analysis)
        findings_by_category = self._group_findings_by_category(analysis.key_findings)

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    @classmethod
    def _generate_summary(
        cls,
        analysis: AssessmentAnalysis,
    ) -> str:
        """Build a concise fallback narrative with fixed assessment-area headings."""
        status = f"Assessment Status: {analysis.assessment_status.value.capitalize()}"
        findings = analysis.key_findings
        if not findings:
            return status

        grouped: dict[str, list[AnalysisFinding]] = {}
        for finding in findings:
            grouped.setdefault(finding.category, []).append(finding)

        paragraphs: list[tuple[str, str]] = []
        ordered_categories = cls._ordered_categories(grouped)
        for category in ordered_categories:
            category_findings = grouped[category]
            profile = [
                finding
                for finding in category_findings
                if finding.rule_id == "PROFILE"
            ]
            triggered = [
                finding
                for finding in category_findings
                if finding.rule_id != "PROFILE"
                and cls._is_triggered(finding)
            ]

            sentences: list[str] = []
            sentences.extend(finding.text.rstrip(".") + "." for finding in profile)
            sentences.extend(finding.text.rstrip(".") + "." for finding in triggered)

            if sentences:
                paragraphs.append((category, " ".join(sentences)))

        narrative = "\n\n".join(
            f"### {category}\n\n{paragraph}"
            if category.casefold() in {area.casefold() for area in cls._ASSESSMENT_AREA_ORDER}
            else paragraph
            for category, paragraph in paragraphs
        )
        return f"{status}\n\n{narrative}"

    @classmethod
    def _ordered_categories(
        cls,
        grouped: dict[str, list[AnalysisFinding]],
    ) -> list[str]:
        """Return production assessment areas first in their authoritative order."""
        canonical = {
            area.casefold(): area
            for area in cls._ASSESSMENT_AREA_ORDER
        }
        ordered: list[str] = []
        for category in cls._ASSESSMENT_AREA_ORDER:
            if category.casefold() in {item.casefold() for item in grouped}:
                ordered.append(category)
        ordered.extend(
            category
            for category in grouped
            if category.casefold() not in canonical
        )
        return ordered

    @staticmethod
    def _validate_rule_evidence(findings: list[AnalysisFinding]) -> None:
        """Reject rule evidence that is not backed by a structured deterministic status."""
        missing_status = [
            finding.rule_id
            for finding in findings
            if finding.rule_id != "PROFILE" and finding.status is None
        ]
        if missing_status:
            rule_ids = ", ".join(missing_status)
            raise ValueError(
                "Rule evidence requires a structured RuleStatus; "
                f"missing status for: {rule_ids}"
            )

    @staticmethod
    def _is_triggered(finding: AnalysisFinding) -> bool:
        """Return whether structured deterministic evidence is triggered."""
        return finding.status == RuleStatus.TRIGGERED

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:
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
