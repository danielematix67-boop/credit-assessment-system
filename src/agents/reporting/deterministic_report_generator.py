from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup
from src.rules.base.status import RuleStatus


class DeterministicReportGenerator(ReportGenerator):
    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        summary = self._generate_summary(analysis)
        findings_by_category = self._group_findings_by_category(analysis.key_findings)

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    @staticmethod
    def _generate_summary(
        analysis: AssessmentAnalysis,
    ) -> str:
        """Build a concise, professional fallback narrative from deterministic evidence."""
        status = f"Assessment Status: {analysis.assessment_status.value.capitalize()}"
        findings = analysis.key_findings
        if not findings:
            return status

        grouped: dict[str, list[AnalysisFinding]] = {}
        for finding in findings:
            grouped.setdefault(finding.category, []).append(finding)

        paragraphs: list[str] = []
        for category_findings in grouped.values():
            profile = [
                finding
                for finding in category_findings
                if finding.rule_id == "PROFILE"
            ]
            triggered = [
                finding
                for finding in category_findings
                if finding.rule_id != "PROFILE"
                and DeterministicReportGenerator._is_triggered(finding)
            ]

            sentences: list[str] = []
            sentences.extend(finding.text.rstrip(".") + "." for finding in profile)
            sentences.extend(finding.text.rstrip(".") + "." for finding in triggered)

            if sentences:
                paragraphs.append(" ".join(sentences))

        narrative = "\n\n".join(paragraphs)
        return f"{status}\n\n{narrative}"

    @staticmethod
    def _is_triggered(finding: AnalysisFinding) -> bool:
        """Return whether evidence is triggered without inspecting narrative text."""
        if finding.status is None:
            # Legacy fixtures created before AnalysisFinding carried RuleStatus.
            return True
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
