from dataclasses import dataclass

from src.models.assessment_status import AssessmentStatus


@dataclass(frozen=True)
class Report:
    position_id: str
    assessment_status: AssessmentStatus
    executive_summary: str
    findings: list[str]
    limitations: list[str]