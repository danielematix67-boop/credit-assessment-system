import time
from datetime import datetime, timezone
from uuid import uuid4

from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.base.agent import Agent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.behavioural_data import BehaviouralData
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.execution_metadata import ExecutionMetadata
from src.models.position import CreditPosition
from src.models.report import Report
from src.services.credit_assessment_case_service import CreditAssessmentCaseService


class AssessmentWorkflow:
    def __init__(
        self,
        credit_case_service: CreditAssessmentCaseService | None = None,
        case_analysis_agent: CaseAnalysisAgent | None = None,
        reporting_agent: Agent[AssessmentAnalysis, Report] | None = None,
        reporting_mode: str = "Unknown",
        *,
        assessment_service: object | None = None,
        analysis_agent: Agent | None = None,
    ) -> None:
        if credit_case_service is None:
            if assessment_service is None:
                raise TypeError(
                    "credit_case_service or assessment_service is required"
                )
            credit_case_service = CreditAssessmentCaseService(assessment_service)

        if case_analysis_agent is None:
            case_analysis_agent = analysis_agent  # type: ignore[assignment]
        if case_analysis_agent is None:
            case_analysis_agent = CaseAnalysisAgent()
        if reporting_agent is None:
            raise TypeError("reporting_agent is required")

        self.credit_case_service = credit_case_service
        self.case_analysis_agent = case_analysis_agent
        self.reporting_agent = reporting_agent
        self.reporting_mode = reporting_mode

        # Compatibility alias for callers still using the pre-case API.
        self.analysis_agent = case_analysis_agent

    def run(
        self,
        position: CreditPosition,
        *,
        behavioural_data: BehaviouralData | None = None,
        debt_sustainability_data: DebtSustainabilityData | None = None,
        customer_profile_data: CustomerProfileData | None = None,
    ) -> AssessmentWorkflowResult:
        execution_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        workflow_start = time.perf_counter()

        assessment_start = time.perf_counter()
        credit_case = self.credit_case_service.assess(
            position,
            behavioural_data=behavioural_data,
            debt_sustainability_data=debt_sustainability_data,
            customer_profile_data=customer_profile_data,
        )
        assessment_elapsed_time = time.perf_counter() - assessment_start

        analysis_start = time.perf_counter()
        if isinstance(self.case_analysis_agent, AnalysisAgent):
            analysis = self.case_analysis_agent.run(
                AssessmentWorkflow._legacy_assessment_from_case(credit_case)
            )
        else:
            analysis = self.case_analysis_agent.run(credit_case)
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
            credit_case=credit_case,
            analysis=analysis,
            report=report,
            execution_metadata=execution_metadata,
            report_generator_used=report_generator_used,
            report_generation_error=report_generation_error,
            assessment_elapsed_time=assessment_elapsed_time,
            analysis_elapsed_time=analysis_elapsed_time,
            reporting_elapsed_time=reporting_elapsed_time,
            total_elapsed_time=total_elapsed_time,
        )

    @staticmethod
    def _legacy_assessment_from_case(credit_case):
        """Project a case back to the legacy Assessment contract."""
        from src.models.assessment import Assessment
        from src.models.assessment_status import AssessmentStatus

        rule_results = [
            result for section in credit_case.sections for result in section.evidence
        ]
        findings = [
            finding for section in credit_case.sections for finding in section.findings
        ]
        status = AssessmentStatus(credit_case.final_assessment.status.value)
        return Assessment(
            position_id=credit_case.position.position_id,
            rule_results=rule_results,
            findings=findings,
            status=status,
        )
