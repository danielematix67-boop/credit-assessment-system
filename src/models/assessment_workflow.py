from dataclasses import dataclass

from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


@dataclass(frozen=True)
class AssessmentWorkflowResult:
    assessment: Assessment
    analysis: AssessmentAnalysis
    report: Report

    report_generator_used: str | None = None
    report_generation_error: str | None = None
