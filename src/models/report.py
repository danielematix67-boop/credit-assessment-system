from dataclasses import dataclass

from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_status import AssessmentStatus


@dataclass(frozen=True)
class ReportFindingGroup:
    category: str
    findings: list[AnalysisFinding]


@dataclass(frozen=True)
class Report:
    position_id: str
    assessment_status: AssessmentStatus
    executive_summary: str
    findings_by_category: list[ReportFindingGroup]
    limitations: list[AnalysisFinding]