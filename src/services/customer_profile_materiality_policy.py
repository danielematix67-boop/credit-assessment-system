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
        fields: set[str] = set()
        for key, value in profile.items():
            if value in (None, "", [], {}):
                continue
            if key in cls._ALWAYS_MATERIAL:
                if isinstance(value, bool) and not value:
                    continue
                fields.add(key)
                continue
            if key in cls._POSITIVE_MATERIAL:
                if isinstance(value, bool):
                    if value:
                        fields.add(key)
                elif isinstance(value, (int, float)):
                    if value > 0:
                        fields.add(key)
                elif value:
                    fields.add(key)
        return fields
