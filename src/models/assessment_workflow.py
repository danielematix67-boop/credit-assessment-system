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

    assessment_elapsed_time: float = 0.0
    analysis_elapsed_time: float = 0.0
    reporting_elapsed_time: float = 0.0
    total_elapsed_time: float = 0.0