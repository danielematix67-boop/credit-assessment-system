from typing import ClassVar


class CustomerProfileMaterialityPolicy:
    """Deterministically select non-rule customer-profile context for executive reporting."""

    _RULE_BACKED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"ews_score_class", "previous_restructuring", "forborne", "business_history_years", "relationship_years"}
    )
    _ALWAYS_MATERIAL: ClassVar[frozenset[str]] = frozenset(
        {
            "ews_score_notching", "ews_score_variation", "active_ewis", "rating", "rating_notching",
            "rating_influential_factors", "rating_elementary_modules", "pd", "minimum_regulatory_risk_grade",
            "previous_risk_grade", "risk_grade_change", "risk_group_interdependence", "risk_group_independence",
            "forborne_non_performing_exit", "protests", "bankruptcies", "litigation", "significant_historical_events",
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
        """Return material contextual fields not already covered by deterministic rules."""
        fields: set[str] = set()
        for key, value in profile.items():
            if key in cls._RULE_BACKED_FIELDS or value in (None, "", [], {}):
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
                elif isinstance(value, (int, float)) and value > 0:
                    fields.add(key)
                elif value:
                    fields.add(key)
        return fields
