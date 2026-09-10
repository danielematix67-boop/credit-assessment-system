from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class DebtSustainabilityAssessmentService:
    """Deterministically assess cash-flow-based debt sustainability indicators."""

    _DSCR_THRESHOLD = 1.00
    _DSCR_HIGH_THRESHOLD = 0.80
    _DEBT_SERVICE_TO_EBITDA_THRESHOLD = 1.00
    _DEBT_SERVICE_TO_EBITDA_HIGH_THRESHOLD = 1.20
    _CASH_FLOW_BUFFER_THRESHOLD = 0.00
    _CASH_FLOW_BUFFER_HIGH_THRESHOLD = -0.20

    def __init__(self, status_calculator: AssessmentStatusCalculator | None = None):
        self.status_calculator = status_calculator or AssessmentStatusCalculator()

    def assess(self, data: DebtSustainabilityData) -> AssessmentSection:
        results = [
            self._dscr_result(data),
            self._debt_service_to_ebitda_result(data),
            self._cash_flow_buffer_result(data),
        ]
        status = self.status_calculator.calculate(results)
        limitations = (
            ["Debt-service and cash-flow data are not available."]
            if all(result.status == RuleStatus.NOT_EVALUABLE for result in results)
            else ["Debt sustainability is assessed from the supplied synthetic inputs only."]
        )

        return AssessmentSection(
            name="Debt Sustainability",
            status=SectionStatus(status.value),
            findings=[],
            evidence=results,
            limitations=limitations,
        )

    @classmethod
    def _dscr_result(cls, data: DebtSustainabilityData) -> RuleResult:
        if data.cash_flow_available_for_debt_service is None or data.debt_service is None:
            return cls._not_evaluable(
                "DS001", "Debt Service Coverage Ratio", "DSCR", cls._DSCR_THRESHOLD,
                SeverityDirection.LOWER_IS_WORSE,
            )
        if data.debt_service <= 0:
            return cls._not_evaluable(
                "DS001", "Debt Service Coverage Ratio",
                "Debt service must be positive to calculate DSCR.", cls._DSCR_THRESHOLD,
                SeverityDirection.LOWER_IS_WORSE,
            )
        value = data.cash_flow_available_for_debt_service / data.debt_service
        return cls._lower_is_worse(
            "DS001", "Debt Service Coverage Ratio", "DSCR", value,
            cls._DSCR_THRESHOLD, cls._DSCR_HIGH_THRESHOLD,
        )

    @classmethod
    def _debt_service_to_ebitda_result(cls, data: DebtSustainabilityData) -> RuleResult:
        if data.debt_service is None or data.ebitda is None:
            return cls._not_evaluable(
                "DS002", "Debt Service / EBITDA", "Debt Service / EBITDA",
                cls._DEBT_SERVICE_TO_EBITDA_THRESHOLD, SeverityDirection.HIGHER_IS_WORSE,
            )
        if data.ebitda <= 0:
            return cls._not_evaluable(
                "DS002", "Debt Service / EBITDA",
                "EBITDA must be positive to calculate Debt Service / EBITDA.",
                cls._DEBT_SERVICE_TO_EBITDA_THRESHOLD, SeverityDirection.HIGHER_IS_WORSE,
            )
        value = data.debt_service / data.ebitda
        return cls._higher_is_worse(
            "DS002", "Debt Service / EBITDA", "Debt Service / EBITDA", value,
            cls._DEBT_SERVICE_TO_EBITDA_THRESHOLD, cls._DEBT_SERVICE_TO_EBITDA_HIGH_THRESHOLD,
        )

    @classmethod
    def _cash_flow_buffer_result(cls, data: DebtSustainabilityData) -> RuleResult:
        if data.cash_flow_available_for_debt_service is None or data.debt_service is None:
            return cls._not_evaluable(
                "DS003", "Cash Flow Debt-Service Buffer", "CFADS - debt service",
                cls._CASH_FLOW_BUFFER_THRESHOLD, SeverityDirection.LOWER_IS_WORSE,
            )
        value = data.cash_flow_available_for_debt_service - data.debt_service
        return cls._lower_is_worse(
            "DS003", "Cash Flow Debt-Service Buffer", "CFADS - debt service", value,
            cls._CASH_FLOW_BUFFER_THRESHOLD, cls._CASH_FLOW_BUFFER_HIGH_THRESHOLD,
        )

    @staticmethod
    def _lower_is_worse(rule_id: str, rule_name: str, indicator: str,
                        value: float, threshold: float, high_threshold: float) -> RuleResult:
        status = RuleStatus.TRIGGERED if value < threshold else RuleStatus.NOT_TRIGGERED
        severity = RuleSeverity.HIGH if value < high_threshold else RuleSeverity.MEDIUM
        reason = (
            f"[{rule_id} - {rule_name}] {indicator} is {value:.2f}, below the threshold of {threshold:.2f}."
            if status == RuleStatus.TRIGGERED
            else f"[{rule_id} - {rule_name}] {indicator} is {value:.2f}, at or above the threshold of {threshold:.2f}."
        )
        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category="Debt Sustainability",
            status=status, value=value, threshold=threshold, severity=severity,
            reason=reason, indicator=indicator, direction=SeverityDirection.LOWER_IS_WORSE,
        )

    @staticmethod
    def _higher_is_worse(rule_id: str, rule_name: str, indicator: str,
                         value: float, threshold: float, high_threshold: float) -> RuleResult:
        status = RuleStatus.TRIGGERED if value > threshold else RuleStatus.NOT_TRIGGERED
        severity = RuleSeverity.HIGH if value > high_threshold else RuleSeverity.MEDIUM
        reason = (
            f"[{rule_id} - {rule_name}] {indicator} is {value:.2f}, above the threshold of {threshold:.2f}."
            if status == RuleStatus.TRIGGERED
            else f"[{rule_id} - {rule_name}] {indicator} is {value:.2f}, at or below the threshold of {threshold:.2f}."
        )
        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category="Debt Sustainability",
            status=status, value=value, threshold=threshold, severity=severity,
            reason=reason, indicator=indicator, direction=SeverityDirection.HIGHER_IS_WORSE,
        )

    @staticmethod
    def _not_evaluable(rule_id: str, rule_name: str, indicator: str,
                       threshold: float, direction: SeverityDirection) -> RuleResult:
        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category="Debt Sustainability",
            status=RuleStatus.NOT_EVALUABLE, value=None, threshold=threshold,
            severity=RuleSeverity.MEDIUM,
            reason=f"[{rule_id} - {rule_name}] {indicator} cannot be evaluated with the available data.",
            indicator=indicator, direction=direction,
        )
