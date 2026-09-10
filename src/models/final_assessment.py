from dataclasses import dataclass, field

from src.models.assessment_section import SectionStatus


@dataclass(frozen=True)
class FinalAssessment:
    """Deterministic aggregation of the macro-area assessment statuses."""

    status: SectionStatus
    evaluated_sections: int
    risk_sections: list[str] = field(default_factory=list)
    normal_sections: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
