from src.models.assessment_section import SectionStatus
from src.models.customer_profile_data import CustomerProfileData
from src.rules.base.status import RuleStatus
from src.services.customer_profile_assessment_service import CustomerProfileAssessmentService


def test_customer_profile_preserves_context_data() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(
            company_name="Synthetic Manufacturing S.p.A.",
            legal_form="S.p.A.",
            sector="Manufacturing",
            shareholders=["Shareholder A", "Shareholder B"],
            relationship_years=8,
        )
    )

    assert section.status == SectionStatus.NORMAL
    assert section.context["company_name"] == "Synthetic Manufacturing S.p.A."
    assert section.context["relationship_years"] == 8


def test_active_ews_triggers_customer_profile_attention() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", active_ews=True)
    )

    assert section.status == SectionStatus.ATTENTION
    assert section.evidence[0].rule_id == "CP001"
    assert section.evidence[0].status == RuleStatus.TRIGGERED
    assert len(section.findings) == 1


def test_two_profile_risk_flags_trigger_critical() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", active_ews=True, previous_restructuring=True)
    )

    assert section.status == SectionStatus.CRITICAL


def test_missing_customer_profile_is_not_evaluable() -> None:
    section = CustomerProfileAssessmentService().assess(CustomerProfileData())

    assert section.status == SectionStatus.NOT_EVALUABLE
    assert section.limitations == ["Customer profile data are not available."]
