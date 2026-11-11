from src.config.final_assessment_policy import FinalAssessmentPolicy
from src.models.assessment_section import SectionStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.final_assessment import FinalAssessment


class FinalAssessmentService:
    """Aggregate macro-area statuses using an external deterministic policy."""

    def __init__(self, policy: FinalAssessmentPolicy | None = None):
        self.policy = policy or FinalAssessmentPolicy.default()

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

        core_attention = [
            section
            for section in attention
            if section.name in self.policy.core_sections
        ]

        if self.policy.critical_if_any_section_critical and critical:
            status = SectionStatus.CRITICAL
            names = ", ".join(section.name for section in critical)
            rationale = (
                "At least one evaluable macro-area is CRITICAL: "
                f"{names}. The policy escalates the overall assessment to CRITICAL "
                "when any macro-area reaches CRITICAL."
            )
        elif len(core_attention) >= self.policy.critical_if_core_attention_at_least:
            status = SectionStatus.CRITICAL
            names = ", ".join(section.name for section in core_attention)
            rationale = (
                f"{len(core_attention)} core macro-areas are classified as ATTENTION "
                f"({names}); the configured escalation threshold is "
                f"{self.policy.critical_if_core_attention_at_least}. "
                "The overall assessment is therefore CRITICAL."
            )
        elif attention:
            status = SectionStatus.ATTENTION
            names = ", ".join(section.name for section in attention)
            rationale = (
                "At least one evaluable macro-area is classified as ATTENTION: "
                f"{names}. No CRITICAL escalation condition was met, so the overall "
                "assessment remains ATTENTION."
            )
        elif (
            self.policy.normal_if_all_evaluable_normal
            and len(evaluable) >= self.policy.normal_requires_min_evaluable_sections
            and len(normal) == len(evaluable)
        ):
            status = SectionStatus.NORMAL
            rationale = (
                f"All {len(evaluable)} evaluable macro-areas are NORMAL, meeting the "
                f"minimum requirement of {self.policy.normal_requires_min_evaluable_sections}. "
                "No deterministic escalation condition was triggered."
            )
        else:
            status = self.policy.no_evaluable_status
            if not evaluable:
                rationale = (
                    "No macro-area could be evaluated with the available evidence. "
                    f"The configured fallback status is {status.value}."
                )
            elif len(evaluable) < self.policy.normal_requires_min_evaluable_sections:
                rationale = (
                    f"Only {len(evaluable)} macro-area(s) could be evaluated; at least "
                    f"{self.policy.normal_requires_min_evaluable_sections} are required "
                    "to assign NORMAL. "
                    f"The configured fallback status is {status.value}."
                )
            else:
                rationale = (
                    "The configured conditions for NORMAL are not satisfied. "
                    f"The configured fallback status is {status.value}."
                )

        limitations = [
            self.policy.not_evaluable_message.format(section=section.name)
            for section in not_evaluable
        ]
        if not_evaluable:
            limitations.append(
                self.policy.partial_evaluation_message.format(
                    evaluable=len(evaluable),
                    total=len(sections),
                )
            )

        return FinalAssessment(
            status=status,
            evaluated_sections=len(evaluable),
            risk_sections=[section.name for section in critical + attention],
            normal_sections=[section.name for section in normal],
            limitations=limitations,
            status_rationale=rationale,
        )
