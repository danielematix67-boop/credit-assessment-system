from pathlib import Path

from src.models.assessment_section import SectionStatus
from src.models.customer_profile_data import CustomerProfileData
from src.models.ews_score import EwsScoreClass
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
            ews_score_class=EwsScoreClass.YELLOW,
            forborne=True,
        )
    )

    assert section.status == SectionStatus.CRITICAL
    assert section.context["company_name"] == "Synthetic Manufacturing S.p.A."
    assert section.context["relationship_years"] == 8
    assert section.context["business_history_years"] == 8
    assert section.context["ews_score_class"] == "YELLOW"
    assert section.context["forborne"] is True


def test_yellow_ews_score_triggers_medium_attention() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(
            company_name="Synthetic Co.",
            ews_score_class=EwsScoreClass.YELLOW,
        )
    )

    result = section.evidence[0]
    assert section.status == SectionStatus.ATTENTION
    assert result.rule_id == "CP001"
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert "YELLOW" in (result.reason or "")
    assert len(section.findings) == 1


def test_orange_ews_score_triggers_medium_attention() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(
            company_name="Synthetic Co.",
            ews_score_class=EwsScoreClass.ORANGE,
        )
    )

    result = section.evidence[0]
    assert section.status == SectionStatus.ATTENTION
    assert result.severity == RuleSeverity.MEDIUM


def test_light_red_ews_score_triggers_high_attention() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(
            company_name="Synthetic Co.",
            ews_score_class=EwsScoreClass.LIGHT_RED,
        )
    )

    result = section.evidence[0]
    assert section.status == SectionStatus.ATTENTION
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.HIGH


def test_green_ews_score_does_not_trigger() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(
            company_name="Synthetic Co.",
            ews_score_class=EwsScoreClass.GREEN,
        )
    )

    result = section.evidence[0]
    assert section.status == SectionStatus.NORMAL
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_forborne_exposure_triggers_medium_attention() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", forborne=True)
    )

    result = section.evidence[3]
    assert section.status == SectionStatus.ATTENTION
    assert result.rule_id == "CP004"
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert result.value is True
    assert len(section.findings) == 1


def test_non_forborne_exposure_does_not_trigger() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", forborne=False)
    )

    result = section.evidence[3]
    assert section.status == SectionStatus.NORMAL
    assert result.rule_id == "CP004"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.severity == RuleSeverity.LOW


def test_forborne_missing_is_not_evaluable() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.")
    )

    result = section.evidence[3]
    assert result.rule_id == "CP004"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == RuleSeverity.MEDIUM


def test_two_profile_risk_flags_trigger_critical() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(
            company_name="Synthetic Co.",
            ews_score_class=EwsScoreClass.LIGHT_RED,
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


def test_business_history_trigger_uses_configured_comment() -> None:
    section = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", business_history_years=4)
    )

    assert section.findings[0].comment.text == (
        "Customer business history is 4 years, indicating limited operating "
        "or customer track record and increased early-stage credit risk."
    )


def test_customer_profile_rule_threshold_is_configuration_driven(tmp_path: Path) -> None:
    config_path = tmp_path / "customer_profile_rules.yaml"
    config_path.write_text(
        "rules:\n"
        "  - rule_id: CP003\n"
        "    rule_name: Business history\n"
        "    indicator: Business history (years)\n"
        "    category: customer_profile\n"
        "    input_field: business_history_years\n"
        "    trigger_operator: LTE\n"
        "    threshold: 7\n"
        "    severity: MEDIUM\n"
        "    severity_direction: LOWER_IS_WORSE\n"
        "    severity_thresholds:\n"
        "      - threshold: 7\n"
        "        severity: MEDIUM\n"
        "      - threshold: 3\n"
        "        severity: HIGH\n"
        "    comment_template: 'Configured history: {value:.0f} years.'\n",
        encoding="utf-8",
    )

    section = CustomerProfileAssessmentService(config_path=config_path).assess(
        CustomerProfileData(company_name="Synthetic Co.", business_history_years=6)
    )

    result = section.evidence[0]
    assert result.threshold == 7.0
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM
    assert section.findings[0].comment.text == "Configured history: 6 years."


def test_missing_customer_profile_is_not_evaluable() -> None:
    section = CustomerProfileAssessmentService().assess(CustomerProfileData())

    assert section.status == SectionStatus.NOT_EVALUABLE
    assert section.limitations == ["Customer profile data are not available."]
