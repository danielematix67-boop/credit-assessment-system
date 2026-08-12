from src.agents.base.agent import Agent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


class ReportingAgent(Agent[AssessmentAnalysis, Report]):

    def run(
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

def test_reporting_agent_handles_empty_analysis():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.NORMAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = ReportingAgent().run(analysis)

    assert report.position_id == "POS001"
    assert report.assessment_status == AssessmentStatus.NORMAL
    assert report.findings == []
    assert report.limitations == []
    assert report.executive_summary == (
        "The credit assessment is classified as normal."
    )

def test_reporting_agent_handles_empty_analysis():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.NORMAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = ReportingAgent().run(analysis)

    assert report.position_id == "POS001"
    assert report.assessment_status == AssessmentStatus.NORMAL
    assert report.findings == []
    assert report.limitations == []
    assert report.executive_summary == (
        "The credit assessment is classified as normal."
    )