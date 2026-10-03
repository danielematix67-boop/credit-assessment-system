from src.services.customer_profile_materiality_policy import (
    CustomerProfileMaterialityPolicy,
)


def test_materiality_selects_non_rule_risk_and_event_context() -> None:
    fields = CustomerProfileMaterialityPolicy.material_fields(
        {
            "sector": "Manufacturing",
            "ews_score_class": "LIGHT_RED",
            "previous_risk_grade": "Performing",
            "risk_grade_change": "Downgrade",
            "ews_score_notching": -2,
            "active_ewis": ["Revenue deterioration"],
            "rating": "BB-",
            "pd": 0.082,
            "past_due_count": 4,
            "generational_transition": True,
            "previous_restructuring": True,
            "protests": ["Protest 1"],
        }
    )

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
    assert "sector" not in fields


def test_materiality_excludes_rule_backed_and_neutral_context() -> None:
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
        }
    )

    assert fields == set()
