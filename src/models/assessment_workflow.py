from dataclasses import dataclass
from typing import Any

from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.execution_metadata import ExecutionMetadata
from src.models.report import Report


@dataclass(frozen=True)
class AssessmentWorkflowResult:
    credit_case: CreditAssessmentCase
    analysis: AssessmentAnalysis
    report: Report
    execution_metadata: ExecutionMetadata | None = None

    report_generator_used: str | None = None
    report_generation_error: str | None = None

    assessment_elapsed_time: float = 0.0
    analysis_elapsed_time: float = 0.0
    reporting_elapsed_time: float = 0.0
    total_elapsed_time: float = 0.0

    @property
    def assessment(self) -> Assessment:
        """Return the legacy deterministic assessment projection."""
        from src.agents.workflow.assessment_workflow import AssessmentWorkflow

        return AssessmentWorkflow._legacy_assessment_from_case(self.credit_case)

    @property
    def rule_results(self) -> list[Any]:
        """Return the complete deterministic evidence from all assessment sections."""
        return [
            result
            for section in self.credit_case.sections
            for result in section.evidence
        ]
