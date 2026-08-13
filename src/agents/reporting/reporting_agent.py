from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


class ReportingAgent(Agent[AssessmentAnalysis, Report]):

    def __init__(
        self,
        report_generator: ReportGenerator,
        fallback_generator: ReportGenerator | None = None,
    ):
        self.report_generator = report_generator
        self.fallback_generator = fallback_generator

    def run(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        try:
            return self.report_generator.generate(analysis)

        except Exception:
            if self.fallback_generator is None:
                raise

            return self.fallback_generator.generate(analysis)