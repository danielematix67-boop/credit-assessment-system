from dataclasses import dataclass

from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.execution_metadata import ExecutionMetadata
from src.models.report import Report


@dataclass(frozen=True)
class AssessmentWorkflowResult:
    assessment: Assessment
    analysis: AssessmentAnalysis
    report: Report
    credit_case: CreditAssessmentCase | None = None
    execution_metadata: ExecutionMetadata | None = None

    report_generator_used: str | None = None
    report_generation_error: str | None = None

    assessment_elapsed_time: float = 0.0
    analysis_elapsed_time: float = 0.0
    reporting_elapsed_time: float = 0.0
    total_elapsed_time: float = 0.0

    @property
    def rule_results(self) -> list:
        """Return the complete deterministic rule evidence for the workflow.

        The case-level assessment is authoritative when available, while the
        legacy Assessment remains the fallback for older workflow executions.
        """
        if self.credit_case is not None:
            results = [
                result
                for section in self.credit_case.sections
                for result in section.evidence
            ]
            if results:
                return results
        return list(self.assessment.rule_results)
