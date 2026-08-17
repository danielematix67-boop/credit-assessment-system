import time

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

        # ----------------------------------------------------
        # Deterministic assessment
        # ----------------------------------------------------

        assessment_start = time.perf_counter()

        assessment = self.assessment_service.assess(position)

        assessment_elapsed_time = (
            time.perf_counter() - assessment_start
        )

        # ----------------------------------------------------
        # Deterministic analysis
        # ----------------------------------------------------

        analysis_start = time.perf_counter()

        analysis = self.analysis_agent.run(assessment)

        analysis_elapsed_time = (
            time.perf_counter() - analysis_start
        )

        # ----------------------------------------------------
        # Reporting
        # ----------------------------------------------------

        reporting_start = time.perf_counter()

        report = self.reporting_agent.run(analysis)

        reporting_elapsed_time = (
            time.perf_counter() - reporting_start
        )

        # ----------------------------------------------------
        # Reporting provenance
        # ----------------------------------------------------

        report_generator_used = getattr(
            self.reporting_agent,
            "last_generator_used",
            None,
        )

        report_generation_error = getattr(
            self.reporting_agent,
            "last_error",
            None,
        )

        # ----------------------------------------------------
        # Total workflow time
        # ----------------------------------------------------

        total_elapsed_time = (
            assessment_elapsed_time
            + analysis_elapsed_time
            + reporting_elapsed_time
        )

        return AssessmentWorkflowResult(
            assessment=assessment,
            analysis=analysis,
            report=report,
            report_generator_used=report_generator_used,
            report_generation_error=report_generation_error,
            assessment_elapsed_time=assessment_elapsed_time,
            analysis_elapsed_time=analysis_elapsed_time,
            reporting_elapsed_time=reporting_elapsed_time,
            total_elapsed_time=total_elapsed_time,
        )