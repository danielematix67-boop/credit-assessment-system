from src.services.customer_profile_materiality_policy import (
    CustomerProfileMaterialityPolicy,
)


def test_materiality_keeps_context_and_non_rule_risk_evidence() -> None:
    fields = CustomerProfileMaterialityPolicy.material_fields(
        {
            "company_name": "Example S.p.A.",
            "counterparty_type": "Corporate",
            "legal_form": "S.p.A.",
            "sector": "Manufacturing",
            "founding_year": 1985,
            "size_class": "Medium",
            "geography": "Northern Italy",
            "operations": "Manufactures industrial components",
            "ews_score_class": "LIGHT_RED",
            "previous_risk_grade": "Performing",
            "risk_grade_change": "Bonis to Past Due",
            "ews_score_notching": "Downward notching",
            "active_ewis": ["Revenue deterioration"],
            "rating": "BB-",
            "rating_notching": "Downward notching",
            "pd": 0.082,
            "past_due_count": 4,
            "generational_transition": True,
            "previous_restructuring": True,
            "protests": ["Protest 1"],
            "shareholder_details": ["Shareholder A: 60%"],
            "credit_facility_details": ["Revolving credit facility"],
            "management_members": ["Managing Director"],
        }
    )

    assert "company_name" in fields
    assert "counterparty_type" in fields
    assert "legal_form" in fields
    assert "sector" in fields
    assert "founding_year" in fields
    assert "size_class" in fields
    assert "geography" in fields
    assert "operations" in fields
    assert "ews_score_class" not in fields
    assert "active_ewis" in fields
    assert "previous_risk_grade" in fields
    assert "risk_grade_change" in fields
    assert "rating" in fields
    assert "pd" in fields
    assert "past_due_count" in fields
    assert "generational_transition" in fields
    assert "previous_restructuring" not in fields
    assert "protests" in fields
    assert "shareholder_details" in fields
    assert "credit_facility_details" in fields
    assert "management_members" in fields


def test_materiality_excludes_rule_backed_fields_and_non_material_zeros() -> None:
    fields = CustomerProfileMaterialityPolicy.material_fields(
        {
            "company_name": "Example S.p.A.",
            "sector": "Manufacturing",
            "geography": "Northern Italy",
            "business_history_years": 1,
            "relationship_years": 2,
            "previous_restructuring": True,
            "forborne": True,
            "ews_score_class": "LIGHT_RED",
            "past_due_count": 0,
            "generational_transition": False,
            "monitoring_period_days": 0,
            "unknown_context_field": "Context added by a future workbook version",
        }
    )

    assert "company_name" in fields
    assert "sector" in fields
    assert "geography" in fields
    assert "unknown_context_field" in fields
    assert "business_history_years" not in fields
    assert "relationship_years" not in fields
    assert "previous_restructuring" not in fields
    assert "forborne" not in fields
    assert "ews_score_class" not in fields
    assert "past_due_count" not in fields
    assert "generational_transition" not in fields
    assert "monitoring_period_days" not in fields
