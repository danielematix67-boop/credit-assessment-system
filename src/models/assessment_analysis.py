from dataclasses import dataclass

from src.models.assessment_status import AssessmentStatus


@dataclass(frozen=True)
class AssessmentAnalysis:
    position_id: str
    assessment_status: AssessmentStatus
    key_findings: list[str]
    risk_factors: list[str]
    limitations: list[str]