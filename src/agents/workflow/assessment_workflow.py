import time
from datetime import datetime, timezone
from uuid import uuid4

from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.execution_metadata import ExecutionMetadata
from src.models.position import CreditPosition
from src.models.report import Report
from src.services.assessment_service import AssessmentService
from src.services.credit_assessment_case_service import CreditAssessmentCaseService


class AssessmentWorkflow:
    def __init__(
        self,
        assessment_service: AssessmentService,
        analysis_agent: Agent[Assessment, AssessmentAnalysis],
        reporting_agent: Agent[AssessmentAnalysis, Report],
        reporting_mode: str = "Unknown",
        credit_case_service: CreditAssessmentCaseService | None = None,
    ) -> None:
        self.assessment_service = assessment_service
        self.analysis_agent = analysis_agent
        self.reporting_agent = reporting_agent
        self.reporting_mode = reporting_mode
        self.credit_case_service = credit_case_service

    def run(self, position: CreditPosition) -> AssessmentWorkflowResult:
        execution_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        workflow_start = time.perf_counter()

        assessment_start = time.perf_counter()
        assessment = self.assessment_service.assess(position)
        assessment_elapsed_time = time.perf_counter() - assessment_start

        credit_case: CreditAssessmentCase | None = None
        if self.credit_case_service is not None:
            credit_case = self.credit_case_service.assess(position)

        analysis_start = time.perf_counter()
        analysis = self.analysis_agent.run(assessment)
        analysis_elapsed_time = time.perf_counter() - analysis_start

        reporting_start = time.perf_counter()
        report = self.reporting_agent.run(analysis)
        reporting_elapsed_time = time.perf_counter() - reporting_start

        report_generator_used = getattr(self.reporting_agent, "last_generator_used", None)
        report_generation_error = getattr(self.reporting_agent, "last_error", None)
        error_category = getattr(self.reporting_agent, "last_error_category", None)
        total_elapsed_time = time.perf_counter() - workflow_start

        execution_metadata = ExecutionMetadata(
            execution_id=execution_id,
            started_at=started_at,
            reporting_mode=self.reporting_mode,
            generator_used=report_generator_used,
            fallback_used=report_generator_used == "FALLBACK",
            error_category=error_category,
            assessment_elapsed_time=assessment_elapsed_time,
            analysis_elapsed_time=analysis_elapsed_time,
            reporting_elapsed_time=reporting_elapsed_time,
            total_elapsed_time=total_elapsed_time,
        )

        return AssessmentWorkflowResult(
            assessment=assessment,
            analysis=analysis,
            report=report,
            credit_case=credit_case,
            execution_metadata=execution_metadata,
            report_generator_used=report_generator_used,
            report_generation_error=report_generation_error,
            assessment_elapsed_time=assessment_elapsed_time,
            analysis_elapsed_time=analysis_elapsed_time,
            reporting_elapsed_time=reporting_elapsed_time,
            total_elapsed_time=total_elapsed_time,
        )
