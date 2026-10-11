from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R015")
class TradeReceivablesGrowthGapRule(Rule):
    """Flag trade receivables growing materially faster than revenue."""

    def evaluate(self, position: CreditPosition) -> RuleResult:
        inputs = (
            ("trade_receivables_current", position.trade_receivables_current),
            ("trade_receivables_1y_ago", position.trade_receivables_1y_ago),
            ("revenue", position.revenue),
            ("revenue_1y_ago", position.revenue_1y_ago),
        )

        values: dict[str, float] = {}
        for field_name, raw_value in inputs:
            if raw_value is None:
                return self._not_evaluable(
                    reason=f"Required receivables-growth input is missing: {field_name}.",
                )
            if (
                not isinstance(raw_value, (int, float))
                or isinstance(raw_value, bool)
                or not isfinite(raw_value)
            ):
                return self._not_evaluable(
                    reason=f"{field_name} must be finite and numeric.",
                )
            if raw_value < 0:
                return self._not_evaluable(
                    reason=f"{field_name} cannot be negative.",
                )
            values[field_name] = float(raw_value)

        receivables_prior = values["trade_receivables_1y_ago"]
        revenue_prior = values["revenue_1y_ago"]
        if receivables_prior <= 0:
            return self._not_evaluable(
                reason=(
                    "Prior-year trade receivables must be positive to calculate "
                    "their percentage growth."
                ),
            )
        if revenue_prior <= 0:
            return self._not_evaluable(
                reason=(
                    "Prior-year revenue must be positive to calculate "
                    "its percentage growth."
                ),
            )

        receivables_growth = (
            values["trade_receivables_current"] - receivables_prior
        ) / receivables_prior
        revenue_growth = (
            values["revenue"] - revenue_prior
        ) / revenue_prior
        growth_gap = receivables_growth - revenue_growth
        triggered = self._is_triggered(growth_gap)

        if triggered:
            reason = (
                f"Trade receivables grew by {receivables_growth:.1%}, while "
                f"revenue grew by {revenue_growth:.1%}; the gap of "
                f"{growth_gap:.1%} exceeds the configured threshold, potentially "
                "indicating slower collections or weaker cash conversion."
            )
        else:
            reason = (
                f"Trade receivables grew by {receivables_growth:.1%}, while "
                f"revenue grew by {revenue_growth:.1%}; the gap is "
                f"{growth_gap:.1%}, not above the configured threshold."
            )

        return self._result(
            value=growth_gap,
            status=RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED,
            reason=reason,
            severity=self._severity(growth_gap) if triggered else RuleSeverity.LOW,
        )
