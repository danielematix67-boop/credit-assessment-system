from src.models.assessment_section import SectionStatus
from src.models.customer_profile_data import CustomerProfileData
from src.rules.base.severity import RuleSeverity
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
            business_history_years=8,
        )
    )

    assert section.status == SectionStatus.NORMAL
    assert section.context["company_name"] == "Synthetic Manufacturing S.p.A."
    assert section.context["relationship_years"] == 8
    assert section.context["business_history_years"] == 8


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
        CustomerProfileData(
            company_name="Synthetic Co.",
            active_ews=True,
            previous_restructuring=True,
        )
    )

    assert section.status == SectionStatus.CRITICAL


def test_business_history_at_five_years_triggers_medium_risk() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", business_history_years=5)
    )

    result = section.evidence[2]
    assert section.status == SectionStatus.ATTENTION
    assert result.rule_id == "CP003"
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert result.value == 5.0
    assert result.threshold == 5.0
    assert len(section.findings) == 1


def test_business_history_at_two_years_triggers_high_risk() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", business_history_years=2)
    )

    result = section.evidence[2]
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_business_history_above_threshold_is_not_triggered() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", business_history_years=6)
    )

    result = section.evidence[2]
    assert section.status == SectionStatus.NORMAL
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


def test_business_history_missing_is_not_evaluable() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.")
    )

    result = section.evidence[2]
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == RuleSeverity.MEDIUM


def test_business_history_trigger_uses_predefined_comment() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", business_history_years=4)
    )

    assert section.findings[0].comment.text == (
        "Customer business history is 4 years, indicating limited operating "
        "or customer track record and increased early-stage credit risk."
    )


def test_missing_customer_profile_is_not_evaluable() -> None:
    section = CustomerProfileAssessmentService().assess(CustomerProfileData())

    assert section.status == SectionStatus.NOT_EVALUABLE
    assert section.limitations == ["Customer profile data are not available."]
