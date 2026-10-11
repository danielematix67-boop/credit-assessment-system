from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R012")
class AveragePaymentDaysIncreaseRule(Rule):
    """Detect payment days materially above the historical average level."""

    _PAYMENT_DAY_FIELDS = (
        "avg_payment_days_current",
        "avg_payment_days_1y_ago",
        "avg_payment_days_2y_ago",
        "avg_payment_days_3y_ago",
        "avg_payment_days_4y_ago",
    )

    def evaluate(self, position: CreditPosition) -> RuleResult:
        payment_day_levels: list[float] = []
        for field_name in self._PAYMENT_DAY_FIELDS:
            raw_value = getattr(position, field_name)
            if raw_value is None:
                return self._not_evaluable(
                    reason=(
                        "Required historical average-payment-days input is missing: "
                        f"{field_name}."
                    ),
                )
            if (
                not isinstance(raw_value, (int, float))
                or not isfinite(raw_value)
            ):
                return self._not_evaluable(
                    reason=(
                        f"Average-payment-days input {field_name} "
                        "must be finite and numeric."
                    ),
                )
            if raw_value < 0:
                return self._not_evaluable(
                    reason=(
                        f"Average-payment-days input {field_name} "
                        "cannot be negative."
                    ),
                )
            payment_day_levels.append(float(raw_value))

        current_days = payment_day_levels[0]
        historical_levels = payment_day_levels[1:]
        historical_average = sum(historical_levels) / len(historical_levels)
        deviation = current_days - historical_average
        triggered = self._is_triggered(deviation)

        if not triggered:
            reason = (
                f"Current average payment days are {current_days:.1f}, versus "
                f"a four-year historical average of {historical_average:.1f}; "
                f"the difference is {deviation:.1f} days, not above the "
                "configured trigger."
            )
        else:
            reason = (
                f"Current average payment days are {current_days:.1f}, versus "
                f"a four-year historical average of {historical_average:.1f}; "
                f"the difference of {deviation:.1f} days exceeds the "
                "configured trigger, potentially indicating liquidity pressure "
                "or greater reliance on supplier credit."
            )

        return self._result(
            value=deviation,
            status=(
                RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED
            ),
            reason=reason,
            severity=self._severity(deviation) if triggered else RuleSeverity.LOW,
        )
