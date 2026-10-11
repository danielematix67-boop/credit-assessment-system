from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R014")
class AverageCollectionDaysIncreaseRule(Rule):
    """Detect collection days materially above the historical average level."""

    _COLLECTION_DAY_FIELDS = (
        "avg_collection_days_current",
        "avg_collection_days_1y_ago",
        "avg_collection_days_2y_ago",
        "avg_collection_days_3y_ago",
        "avg_collection_days_4y_ago",
    )

    def evaluate(self, position: CreditPosition) -> RuleResult:
        collection_day_levels: list[float] = []
        for field_name in self._COLLECTION_DAY_FIELDS:
            raw_value = getattr(position, field_name)
            if raw_value is None:
                return self._not_evaluable(
                    reason=(
                        "Required historical average-collection-days input is missing: "
                        f"{field_name}."
                    ),
                )
            if (
                not isinstance(raw_value, (int, float))
                or isinstance(raw_value, bool)
                or not isfinite(raw_value)
            ):
                return self._not_evaluable(
                    reason=(
                        f"Average-collection-days input {field_name} "
                        "must be finite and numeric."
                    ),
                )
            if raw_value < 0:
                return self._not_evaluable(
                    reason=(
                        f"Average-collection-days input {field_name} "
                        "cannot be negative."
                    ),
                )
            collection_day_levels.append(float(raw_value))

        current_days = collection_day_levels[0]
        historical_levels = collection_day_levels[1:]
        historical_average = sum(historical_levels) / len(historical_levels)
        deviation = current_days - historical_average
        triggered = self._is_triggered(deviation)

        if triggered:
            reason = (
                f"Current average collection days are {current_days:.1f}, versus "
                f"a four-year historical average of {historical_average:.1f}; "
                f"the increase of {deviation:.1f} days exceeds the configured "
                "trigger, potentially indicating slower customer payments, "
                "weaker cash conversion or increased working-capital pressure."
            )
        else:
            reason = (
                f"Current average collection days are {current_days:.1f}, versus "
                f"a four-year historical average of {historical_average:.1f}; "
                f"the difference is {deviation:.1f} days, not above the "
                "configured trigger."
            )

        return self._result(
            value=deviation,
            status=RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED,
            reason=reason,
            severity=self._severity(deviation) if triggered else RuleSeverity.LOW,
        )
