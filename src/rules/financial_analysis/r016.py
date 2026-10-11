from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R016")
class IntangibleAssetsConcentrationRule(Rule):
    """Flag a material concentration of intangible assets in total assets."""

    def evaluate(self, position: CreditPosition) -> RuleResult:
        intangible_assets = position.intangible_assets
        total_assets = position.total_assets

        for field_name, value in (
            ("intangible_assets", intangible_assets),
            ("total_assets", total_assets),
        ):
            if value is None:
                return self._not_evaluable(
                    reason=f"Required intangible-assets input is missing: {field_name}.",
                )
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(value)
            ):
                return self._not_evaluable(
                    reason=f"{field_name} must be finite and numeric.",
                )

        assert intangible_assets is not None
        assert total_assets is not None

        if intangible_assets < 0:
            return self._not_evaluable(
                reason="Intangible assets cannot be negative.",
            )
        if total_assets <= 0:
            return self._not_evaluable(
                reason="Total assets must be positive to calculate intangible-assets concentration.",
            )
        if intangible_assets > total_assets:
            return self._not_evaluable(
                reason="Intangible assets cannot exceed total assets.",
            )

        incidence = intangible_assets / total_assets
        triggered = self._is_triggered(incidence)

        if triggered:
            reason = (
                f"Intangible assets represent {incidence:.1%} of total assets, "
                "exceeding the configured threshold. This concentration may warrant "
                "review of capitalization policies, asset recognition and "
                "recoverability; it is a risk indicator, not evidence of improper "
                "accounting by itself."
            )
        else:
            reason = (
                f"Intangible assets represent {incidence:.1%} of total assets, "
                "which does not exceed the configured threshold."
            )

        return self._result(
            value=incidence,
            status=RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED,
            reason=reason,
            severity=self._severity(incidence) if triggered else RuleSeverity.LOW,
        )
