from dataclasses import dataclass
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


@dataclass
class AssessmentWorkflowResult:
    assessment: Assessment
    analysis: AssessmentAnalysis
    report: Report