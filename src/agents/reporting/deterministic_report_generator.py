from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


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
        findings = analysis.key_findings
        if not findings:
            return "No deterministic reporting evidence is available for this assessment."

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
                and "cannot be evaluated" not in finding.text.lower()
                and "does not meet the deterministic trigger condition" not in finding.text.lower()
            ]
            not_evaluable = [
                finding
                for finding in category_findings
                if "cannot be evaluated" in finding.text.lower()
            ]
            not_triggered = [
                finding
                for finding in category_findings
                if "does not meet the deterministic trigger condition" in finding.text.lower()
            ]

            sentences: list[str] = []
            sentences.extend(finding.text.rstrip(".") + "." for finding in profile)
            sentences.extend(finding.text.rstrip(".") + "." for finding in triggered)

            if not_triggered:
                sentences.append(
                    f"{len(not_triggered)} monitored indicator"
                    f"{'s' if len(not_triggered) != 1 else ''} did not meet the deterministic trigger condition."
                )

            if not_evaluable:
                sentences.append(
                    f"{len(not_evaluable)} indicator"
                    f"{'s' if len(not_evaluable) != 1 else ''} could not be evaluated because sufficiently reliable values were unavailable."
                )

            if sentences:
                paragraphs.append(" ".join(sentences))

        return "\n\n".join(paragraphs)

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
