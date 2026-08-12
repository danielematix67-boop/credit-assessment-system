from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


class DeterministicReportGenerator(ReportGenerator):

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        if analysis.assessment_status == AssessmentStatus.NORMAL:
            summary = (
                "The credit assessment is classified as normal."
            )

        elif analysis.assessment_status == AssessmentStatus.ATTENTION:
            summary = (
                "The credit assessment requires attention."
            )

        elif analysis.assessment_status == AssessmentStatus.CRITICAL:
            summary = (
                "The credit assessment is classified as critical."
            )

        else:
            summary = (
                "The credit assessment has an undefined status."
            )

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=summary,
            findings=analysis.key_findings,
            limitations=analysis.limitations,
        )