from dataclasses import dataclass, field

from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_status import AssessmentStatus


@dataclass(frozen=True)
class AssessmentAnalysis:
    position_id: str
    assessment_status: AssessmentStatus
    key_findings: list[AnalysisFinding]
    risk_factors: list[AnalysisFinding]
    limitations: list[AnalysisFinding]
    # Complete deterministic rule evidence, including triggered, non-triggered
    # and non-evaluable rules across every assessment macro-area.
    rule_evidence: list[AnalysisFinding] = field(default_factory=list)
