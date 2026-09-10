from dataclasses import dataclass

from src.models.assessment_section import AssessmentSection
from src.models.final_assessment import FinalAssessment
from src.models.position import CreditPosition


@dataclass(frozen=True)
class CreditAssessmentCase:
    """Container for the macro-areas of a credit analysis process."""

    position: CreditPosition
    customer_profile: AssessmentSection
    financial_analysis: AssessmentSection
    behavioural_analysis: AssessmentSection
    debt_sustainability: AssessmentSection
    final_assessment: FinalAssessment | None = None

    @property
    def sections(self) -> list[AssessmentSection]:
        """Return sections in the order followed by a credit analyst."""
        return [
            self.customer_profile,
            self.financial_analysis,
            self.behavioural_analysis,
            self.debt_sustainability,
        ]
