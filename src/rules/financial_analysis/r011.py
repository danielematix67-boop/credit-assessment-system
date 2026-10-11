from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R011")
class TradePayablesIncreaseRule(Rule):
    """Detect acceleration in trade payables versus historical growth."""

    _PAYABLE_FIELDS = (
        "trade_payables_current",
        "trade_payables_1y_ago",
        "trade_payables_2y_ago",
        "trade_payables_3y_ago",
        "trade_payables_4y_ago",
    )

    def evaluate(self, position: CreditPosition) -> RuleResult:
        payable_levels: list[float] = []
        for field_name in self._PAYABLE_FIELDS:
            raw_value = getattr(position, field_name)
            if raw_value is None:
                return self._not_evaluable(
                    reason=(
                        "Required historical trade-payables input is missing: "
                        f"{field_name}."
                    ),
                )
            if (
                not isinstance(raw_value, (int, float))
                or not isfinite(raw_value)
            ):
                return self._not_evaluable(
                    reason=(
                        f"Historical trade-payables input {field_name} "
                        "must be finite and numeric."
                    ),
                )
            if raw_value < 0:
                return self._not_evaluable(
                    reason=(
                        f"Historical trade-payables input {field_name} "
                        "cannot be negative."
                    ),
                )
            payable_levels.append(float(raw_value))

        if payable_levels[1] <= 0:
            return self._not_evaluable(
                reason=(
                    "Trade payables one year ago must be positive to "
                    "calculate current growth."
                ),
            )

        historical_growth: list[float] = []
        for newer, older in zip(payable_levels[1:4], payable_levels[2:5]):
            if older <= 0:
                return self._not_evaluable(
                    reason=(
                        "Historical trade-payables bases must be positive "
                        "to calculate growth."
                    ),
                )
            historical_growth.append((newer - older) / older)

        current_growth = (payable_levels[0] - payable_levels[1]) / payable_levels[1]
        historical_average = sum(historical_growth) / len(historical_growth)
        deviation = current_growth - historical_average
        triggered = current_growth > 0 and self._is_triggered(deviation)

        if current_growth <= 0:
            reason = (
                "Trade payables are not increasing in the latest year "
                f"(current growth: {current_growth:.1%}); no trigger."
            )
        elif not triggered:
            reason = (
                f"Current trade-payables growth is {current_growth:.1%}, compared "
                f"with historical average growth of {historical_average:.1%}; "
                f"the acceleration is {deviation:.1%}, below the configured trigger."
            )
        else:
            reason = (
                f"Current trade-payables growth is {current_growth:.1%}, compared "
                f"with historical average growth of {historical_average:.1%}; "
                f"the acceleration of {deviation:.1%} exceeds the configured trigger."
            )

        return self._result(
            value=deviation,
            status=(
                RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED
            ),
            reason=reason,
            severity=self._severity(deviation) if triggered else RuleSeverity.LOW,
        )
