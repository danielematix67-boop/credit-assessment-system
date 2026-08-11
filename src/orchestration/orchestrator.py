from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.position import CreditPosition
from src.models.report import Report
from src.services.assessment_service import AssessmentService


class AssessmentOrchestrator:

    def __init__(
        self,
        assessment_service: AssessmentService,
        reporting_agent: ReportingAgent,
    ):
        self.assessment_service = assessment_service
        self.reporting_agent = reporting_agent

    def run(self, position: CreditPosition) -> Report:
        assessment = self.assessment_service.assess(position)

        return self.reporting_agent.run(assessment)