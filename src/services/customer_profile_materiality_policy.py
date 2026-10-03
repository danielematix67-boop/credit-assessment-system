from typing import ClassVar


class CustomerProfileMaterialityPolicy:
    """Deterministically select customer-profile context for executive reporting."""

    _ALWAYS_MATERIAL: ClassVar[frozenset[str]] = frozenset(
        {
            "ews_score_class",
            "ews_score_notching",
            "ews_score_variation",
            "active_ewis",
            "rating",
            "rating_increments",
            "rating_influential_factors",
            "rating_elementary_modules",
            "pd",
            "minimum_regulatory_risk_grade",
            "risk_group_interdependence",
            "risk_group_independence",
            "previous_restructuring",
            "forborne",
            "forborne_non_performing_exit",
            "protests",
            "bankruptcies",
            "litigation",
            "significant_historical_events",
        }
    )
    _POSITIVE_MATERIAL: ClassVar[frozenset[str]] = frozenset(
        {
            "past_due_count",
            "cure_period_days",
            "monitoring_period_days",
            "probation_period_days",
            "generational_transition",
        }
    )

    @classmethod
    def material_fields(cls, profile: dict[str, object]) -> set[str]:
        """Return fields that should enter the executive summary."""
        fields = {
            key
            for key, value in profile.items()
            if value not in (None, "", [], {})
            and (
                key in cls._ALWAYS_MATERIAL
                or key in cls._POSITIVE_MATERIAL
            )
        }
        return fields
