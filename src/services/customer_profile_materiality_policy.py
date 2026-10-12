from typing import ClassVar


class CustomerProfileMaterialityPolicy:
    """Select populated customer-profile context not already covered by rules."""

    _RULE_BACKED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "ews_score_class",
            "previous_restructuring",
            "forborne",
            "business_history_years",
            "relationship_years",
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
        """Keep all populated context except rule-backed fields and non-material zeros.

        Descriptive information such as sector, company size, operations, ownership,
        management and banking facilities remains reportable even when it does not
        trigger a deterministic rule. Rule-backed fields are omitted here to avoid
        duplicating the corresponding deterministic rule evidence in the narrative.
        """
        fields: set[str] = set()
        for key, value in profile.items():
            if key in cls._RULE_BACKED_FIELDS or value in (None, "", [], {}):
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
                continue

            fields.add(key)

        return fields
