from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
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
        if analysis.assessment_status == AssessmentStatus.NORMAL:
            summary = (
                "Assessment status: NORMAL.\n\n"
                "The credit assessment does not identify "
                "significant risk factors."
            )

        elif analysis.assessment_status == AssessmentStatus.ATTENTION:
            summary = (
                "Assessment status: ATTENTION.\n\n"
                "The credit assessment identifies some "
                "elements requiring monitoring."
            )

        elif analysis.assessment_status == AssessmentStatus.CRITICAL:
            summary = (
                "Assessment status: CRITICAL.\n\n"
                "The credit assessment identifies significant "
                "risk factors affecting the credit profile."
            )

        else:
            summary = (
                "Assessment status: UNDEFINED.\n\n"
                "The credit assessment status could not be determined."
            )

        if analysis.risk_factors:
            summary += "\n\nKey risk factors:\n"

            for risk_factor in analysis.risk_factors:
                summary += f"- {risk_factor.text}\n"

        elif analysis.key_findings:
            summary += "\n\nKey findings:\n"

            for finding in analysis.key_findings:
                summary += f"- {finding.text}\n"

        return summary

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
