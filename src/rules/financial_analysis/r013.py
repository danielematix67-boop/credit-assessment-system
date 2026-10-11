from math import isfinite

from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R013")
class TaxDebtConcentrationRule(Rule):
    """Flag tax debt that represents a material share of total liabilities."""

    def evaluate(self, position: CreditPosition) -> RuleResult:
        tax_debt = position.tax_debt
        total_liabilities = position.total_liabilities

        for field_name, value in (
            ("tax_debt", tax_debt),
            ("total_liabilities", total_liabilities),
        ):
            if value is None:
                return self._not_evaluable(
                    reason=f"Required tax-debt input is missing: {field_name}.",
                )
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(value)
            ):
                return self._not_evaluable(
                    reason=f"{field_name} must be finite and numeric.",
                )

        assert tax_debt is not None
        assert total_liabilities is not None

        if tax_debt < 0:
            return self._not_evaluable(
                reason="Tax debt cannot be negative.",
            )
        if total_liabilities <= 0:
            return self._not_evaluable(
                reason="Total liabilities must be positive to calculate tax-debt incidence.",
            )

        incidence = tax_debt / total_liabilities
        triggered = self._is_triggered(incidence)

        if triggered:
            reason = (
                f"Tax debt represents {incidence:.1%} of total liabilities, "
                "exceeding the configured threshold and potentially indicating "
                "material accumulated tax obligations."
            )
        else:
            reason = (
                f"Tax debt represents {incidence:.1%} of total liabilities, "
                "which does not exceed the configured threshold."
            )

        return self._result(
            value=incidence,
            status=RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED,
            reason=reason,
            severity=self._severity(incidence) if triggered else RuleSeverity.LOW,
        )
