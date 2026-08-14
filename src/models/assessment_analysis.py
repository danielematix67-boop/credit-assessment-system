from dataclasses import dataclass

from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_status import AssessmentStatus


@dataclass(frozen=True)
class AssessmentAnalysis:
    position_id: str
    assessment_status: AssessmentStatus
    key_findings: list[AnalysisFinding]
    risk_factors: list[AnalysisFinding]
    limitations: list[AnalysisFinding]