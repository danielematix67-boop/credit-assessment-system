from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R012")
class AveragePaymentDaysIncreaseRule(Rule):
    """Detect acceleration in average payment days versus historical changes."""

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

        # Absolute changes are used because the input is measured in days.
        # The baseline averages the three annual changes before the latest year.
        historical_changes = [
            newer - older
            for newer, older in zip(
                payment_day_levels[1:4],
                payment_day_levels[2:5],
            )
        ]
        current_change = payment_day_levels[0] - payment_day_levels[1]
        historical_average_change = sum(historical_changes) / len(
            historical_changes
        )
        deviation = current_change - historical_average_change
        triggered = current_change > 0 and self._is_triggered(deviation)

        if current_change <= 0:
            reason = (
                "Average payment days have not increased in the latest year "
                f"(current change: {current_change:.1f} days); no trigger."
            )
        elif not triggered:
            reason = (
                f"Average payment days increased by {current_change:.1f} days "
                f"in the latest year, compared with a historical average annual "
                f"change of {historical_average_change:.1f} days; the additional "
                f"increase is {deviation:.1f} days, below the configured trigger."
            )
        else:
            reason = (
                f"Average payment days increased by {current_change:.1f} days "
                f"in the latest year, compared with a historical average annual "
                f"change of {historical_average_change:.1f} days; the additional "
                f"increase of {deviation:.1f} days exceeds the configured trigger."
            )

        return self._result(
            value=deviation,
            status=(
                RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED
            ),
            reason=reason,
            severity=self._severity(deviation) if triggered else RuleSeverity.LOW,
        )
