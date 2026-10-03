from src.services.customer_profile_materiality_policy import (
    CustomerProfileMaterialityPolicy,
)


def test_materiality_selects_risk_and_relevant_event_context() -> None:
    fields = CustomerProfileMaterialityPolicy.material_fields(
        {
            "sector": "Manufacturing",
            "ews_score_class": "LIGHT_RED",
            "active_ewis": ["Revenue deterioration"],
            "rating": "BB-",
            "pd": 0.082,
            "past_due_count": 4,
            "generational_transition": True,
            "previous_restructuring": True,
            "protests": ["Protest 1"],
        }
    )

    assert "ews_score_class" in fields
    assert "active_ewis" in fields
    assert "rating" in fields
    assert "pd" in fields
    assert "past_due_count" in fields
    assert "generational_transition" in fields
    assert "previous_restructuring" in fields
    assert "protests" in fields
    assert "sector" not in fields


def test_materiality_excludes_neutral_or_descriptive_context() -> None:
    fields = CustomerProfileMaterialityPolicy.material_fields(
        {
            "company_name": "Example S.p.A.",
            "sector": "Manufacturing",
            "geography": "Northern Italy",
            "past_due_count": 0,
            "generational_transition": False,
            "previous_restructuring": False,
            "forborne": False,
            "forborne_non_performing_exit": False,
        }
    )

    assert fields == set()
