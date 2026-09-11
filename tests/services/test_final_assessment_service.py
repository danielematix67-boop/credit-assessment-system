from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.services.final_assessment_service import FinalAssessmentService


def _section(name: str, status: SectionStatus) -> AssessmentSection:
    return AssessmentSection(name=name, status=status, findings=[], evidence=[], limitations=[])


def _case(*statuses: SectionStatus) -> CreditAssessmentCase:
    sections = list(statuses) + [SectionStatus.NOT_EVALUABLE] * (4 - len(statuses))
    return CreditAssessmentCase(
        position=CreditPosition(position_id="TEST"),
        customer_profile=_section("Customer Profile", sections[0]),
        financial_analysis=_section("Financial Analysis", sections[1]),
        behavioural_analysis=_section("Behavioural Analysis", sections[2]),
        debt_sustainability=_section("Debt Sustainability", sections[3]),
    )


def test_final_assessment_is_normal_when_all_evaluable_sections_are_normal() -> None:
    result = FinalAssessmentService().assess(_case(SectionStatus.NORMAL, SectionStatus.NORMAL))
    assert result.status == SectionStatus.NORMAL
    assert result.evaluated_sections == 2


def test_final_assessment_is_attention_for_one_attention_section() -> None:
    result = FinalAssessmentService().assess(_case(SectionStatus.ATTENTION, SectionStatus.NORMAL))
    assert result.status == SectionStatus.ATTENTION


def test_final_assessment_is_critical_for_two_core_attention_sections() -> None:
    result = FinalAssessmentService().assess(
        _case(SectionStatus.NORMAL, SectionStatus.ATTENTION, SectionStatus.ATTENTION)
    )
    assert result.status == SectionStatus.CRITICAL


def test_customer_profile_attention_does_not_count_as_core_double_trigger() -> None:
    result = FinalAssessmentService().assess(_case(SectionStatus.ATTENTION, SectionStatus.ATTENTION))
    assert result.status == SectionStatus.ATTENTION


def test_customer_profile_critical_always_escalates_final_assessment() -> None:
    result = FinalAssessmentService().assess(_case(SectionStatus.CRITICAL, SectionStatus.NORMAL))
    assert result.status == SectionStatus.CRITICAL


def test_final_assessment_is_critical_when_any_core_section_is_critical() -> None:
    result = FinalAssessmentService().assess(_case(SectionStatus.NORMAL, SectionStatus.CRITICAL))
    assert result.status == SectionStatus.CRITICAL


def test_final_assessment_is_attention_when_no_section_is_evaluable() -> None:
    result = FinalAssessmentService().assess(_case())
    assert result.status == SectionStatus.ATTENTION
    assert result.evaluated_sections == 0


def test_customer_profile_attention_plus_two_core_attention_is_critical() -> None:
    result = FinalAssessmentService().assess(
        _case(SectionStatus.ATTENTION, SectionStatus.ATTENTION, SectionStatus.ATTENTION)
    )
    assert result.status == SectionStatus.CRITICAL


def test_partial_evaluation_with_all_evaluable_sections_normal_is_normal() -> None:
    result = FinalAssessmentService().assess(
        _case(SectionStatus.NORMAL, SectionStatus.NORMAL, SectionStatus.NOT_EVALUABLE)
    )
    assert result.status == SectionStatus.NORMAL
    assert result.evaluated_sections == 2
    assert len(result.limitations) == 3
