from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report
from src.services.assessment_service import AssessmentService


class AssessmentWorkflow:

    def __init__(
        self,
        assessment_service: AssessmentService,
        analysis_agent: Agent[Assessment, AssessmentAnalysis],
        reporting_agent: Agent[AssessmentAnalysis, Report],
    ):
        self.assessment_service = assessment_service
        self.analysis_agent = analysis_agent
        self.reporting_agent = reporting_agent

    def run(
        self,
        position: CreditPosition,
    ) -> AssessmentWorkflowResult:

        assessment = self.assessment_service.assess(position)

        analysis = self.analysis_agent.run(assessment)

        report = self.reporting_agent.run(analysis)

        return AssessmentWorkflowResult(
            assessment=assessment,
            analysis=analysis,
            report=report,
        )