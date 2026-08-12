from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


class ReportingAgent(Agent[AssessmentAnalysis, Report]):

    def __init__(
        self,
        report_generator: ReportGenerator,
    ):
        self.report_generator = report_generator

    def run(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        return self.report_generator.generate(analysis)