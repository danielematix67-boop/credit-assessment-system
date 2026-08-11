from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.services.assessment_service import AssessmentService


class AssessmentWorkflow:

    def __init__(
        self,
        assessment_service: AssessmentService,
        analysis_agent: AnalysisAgent,
        reporting_agent: ReportingAgent,
    ):
        self.assessment_service = assessment_service
        self.analysis_agent = analysis_agent
        self.reporting_agent = reporting_agent

    def run(self, position) -> AssessmentWorkflowResult:

        assessment = self.assessment_service.assess(position)

        analysis = self.analysis_agent.run(assessment)

        report = self.reporting_agent.run(analysis)

        return AssessmentWorkflowResult(
            assessment=assessment,
            analysis=analysis,
            report=report,
        )