from src.models.assessment_section import SectionStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.final_assessment import FinalAssessment


class FinalAssessmentService:
    """Aggregate macro-area statuses into one deterministic final assessment."""

    def assess(self, case: CreditAssessmentCase) -> FinalAssessment:
        sections = case.sections
        evaluable = [section for section in sections if section.is_evaluable]
        critical = [
            section for section in evaluable if section.status == SectionStatus.CRITICAL
        ]
        attention = [
            section for section in evaluable if section.status == SectionStatus.ATTENTION
        ]
        normal = [
            section for section in evaluable if section.status == SectionStatus.NORMAL
        ]
        not_evaluable = [section for section in sections if not section.is_evaluable]

        # Customer Profile flags are retained as explicit findings, but they
        # do not independently turn a second macro-area attention into CRITICAL.
        # This avoids double-counting contextual risk signals with core
        # financial/behavioural/debt-risk assessments.
        core_attention = [
            section for section in attention if section.name != "Customer Profile"
        ]

        if critical:
            status = SectionStatus.CRITICAL
        elif len(core_attention) >= 2:
            status = SectionStatus.CRITICAL
        elif attention:
            status = SectionStatus.ATTENTION
        elif len(evaluable) >= 2:
            status = SectionStatus.NORMAL
        else:
            status = SectionStatus.ATTENTION

        limitations = [
            f"{section.name} could not be evaluated because sufficient evidence was not available."
            for section in not_evaluable
        ]
        if not_evaluable:
            limitations.append(
                f"Final assessment is based on {len(evaluable)} of {len(sections)} evaluable macro-areas."
            )

        return FinalAssessment(
            status=status,
            evaluated_sections=len(evaluable),
            risk_sections=[section.name for section in critical + attention],
            normal_sections=[section.name for section in normal],
            limitations=limitations,
        )
