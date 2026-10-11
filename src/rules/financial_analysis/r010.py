from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R010")
class SustainedBankDebtIncreaseRule(Rule):
    """Detect a positive acceleration in bank debt versus historical growth."""

    _DEBT_FIELDS = (
        "bank_debt_current",
        "bank_debt_1y_ago",
        "bank_debt_2y_ago",
        "bank_debt_3y_ago",
        "bank_debt_4y_ago",
    )

    def evaluate(self, position: CreditPosition) -> RuleResult:
        debt_levels: list[float] = []
        for field_name in self._DEBT_FIELDS:
            raw_value = getattr(position, field_name)
            if raw_value is None:
                return self._not_evaluable(
                    reason=f"Required historical bank-debt input is missing: {field_name}.",
                )
            if not isinstance(raw_value, (int, float)) or not isfinite(raw_value):
                return self._not_evaluable(
                    reason=f"Historical bank-debt input {field_name} must be finite and numeric.",
                )
            if raw_value < 0:
                return self._not_evaluable(
                    reason=f"Historical bank-debt input {field_name} cannot be negative.",
                )
            debt_levels.append(float(raw_value))

        # The current growth rate compares year t with t-1. The historical
        # baseline averages the three growth rates from t-1 through t-4.
        if debt_levels[1] <= 0:
            return self._not_evaluable(
                reason="Bank debt one year ago must be positive to calculate current growth.",
            )

        historical_growth: list[float] = []
        for newer, older in zip(debt_levels[1:4], debt_levels[2:5]):
            if older <= 0:
                return self._not_evaluable(
                    reason="Historical bank-debt bases must be positive to calculate growth.",
                )
            historical_growth.append((newer - older) / older)

        current_growth = (debt_levels[0] - debt_levels[1]) / debt_levels[1]
        historical_average = sum(historical_growth) / len(historical_growth)
        deviation = current_growth - historical_average
        triggered = current_growth > 0 and self._is_triggered(deviation)

        if current_growth <= 0:
            reason = (
                f"Bank debt is not increasing in the latest year "
                f"(current growth: {current_growth:.1%}); no trigger."
            )
        elif not triggered:
            reason = (
                f"Current bank-debt growth is {current_growth:.1%}, compared with "
                f"historical average growth of {historical_average:.1%}; the "
                f"acceleration is {deviation:.1%}, below the configured trigger."
            )
        else:
            reason = (
                f"Current bank-debt growth is {current_growth:.1%}, compared with "
                f"historical average growth of {historical_average:.1%}; the "
                f"acceleration of {deviation:.1%} exceeds the configured trigger."
            )

        return self._result(
            value=deviation,
            status=(
                RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED
            ),
            reason=reason,
            severity=self._severity(deviation) if triggered else RuleSeverity.LOW,
        )
