from pathlib import Path
from typing import cast

from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.rule_finding import RuleFinding
from src.rules.base.config import RuleConfig
from src.rules.base.severity_policy import SeverityPolicy
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class DebtSustainabilityAssessmentService:
    """Assess debt sustainability using externally configured rule policy."""

    DEFAULT_CONFIG_PATH = Path("config/debt_sustainability_rules.yaml")

    def __init__(
        self,
        status_calculator: AssessmentStatusCalculator | None = None,
        comment_engine: CommentEngine | None = None,
        config_loader: RuleConfigLoader | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.status_calculator = status_calculator or AssessmentStatusCalculator()
        self.comment_engine = comment_engine or CommentEngine()
        self.config_loader = config_loader or RuleConfigLoader()
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH

    def assess(self, data: DebtSustainabilityData) -> AssessmentSection:
        configs = self.config_loader.load(self.config_path)
        results = [self._evaluate_rule(config, data) for config in configs]
        status = self._section_status(results)
        findings = []
        for result in results:
            if result.status != RuleStatus.TRIGGERED:
                continue
            comment = self.comment_engine.generate(result)
            assert comment is not None
            findings.append(RuleFinding(result=result, comment=comment))
        limitations = (
            ["Debt-service and cash-flow data are not available."]
            if all(result.status == RuleStatus.NOT_EVALUABLE for result in results)
            else ["Debt sustainability is assessed from the supplied synthetic inputs only."]
        )
        return AssessmentSection(
            name="Debt Sustainability",
            status=status,
            findings=findings,
            evidence=results,
            limitations=limitations,
        )

    @classmethod
    def _evaluate_rule(cls, config: RuleConfig, data: DebtSustainabilityData) -> RuleResult:
        fields = config.input_fields or ((config.input_field,) if config.input_field else ())
        values = [getattr(data, field, None) for field in fields]
        if not fields or any(value is None for value in values):
            return cls._not_evaluable(config, "Required input data are not available.")

        numeric_values = [cast(float, value) for value in values]
        if config.calculation == "ratio":
            numerator, denominator = numeric_values
            if denominator <= 0:
                return cls._not_evaluable(
                    config, "The denominator must be positive to calculate the indicator."
                )
            value = numerator / denominator
        elif config.calculation == "difference":
            value = numeric_values[0] - numeric_values[1]
        else:
            value = numeric_values[0]

        triggered = cls._compare(value, config.threshold, config.trigger_operator)
        severity = SeverityPolicy(
            direction=config.severity_direction,
            thresholds=config.severity_thresholds,
        ).evaluate(value) or config.severity
        status = RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED
        reason = (
            f"[{config.rule_id} - {config.rule_name}] {config.indicator} is {value:.2f}, "
            f"with configured threshold {config.threshold:.2f}."
        )
        return RuleResult(
            rule_id=config.rule_id,
            rule_name=config.rule_name,
            category=config.category,
            status=status,
            value=value,
            threshold=config.threshold,
            severity=severity,
            reason=reason,
            indicator=config.indicator,
            direction=config.severity_direction,
            comment_template=config.comment_template,
        )

    @staticmethod
    def _compare(value: float, threshold: float, operator: str) -> bool:
        return {
            "GT": value > threshold,
            "GTE": value >= threshold,
            "LT": value < threshold,
            "LTE": value <= threshold,
        }[operator]

    @staticmethod
    def _not_evaluable(config: RuleConfig, reason: str) -> RuleResult:
        return RuleResult(
            rule_id=config.rule_id,
            rule_name=config.rule_name,
            category=config.category,
            status=RuleStatus.NOT_EVALUABLE,
            value=None,
            threshold=config.threshold,
            severity=config.severity,
            reason=f"[{config.rule_id} - {config.rule_name}] {reason}",
            indicator=config.indicator,
            direction=config.severity_direction,
            comment_template=config.comment_template,
        )

    @staticmethod
    def _section_status(results: list[RuleResult]) -> SectionStatus:
        evaluable = [result for result in results if result.status != RuleStatus.NOT_EVALUABLE]
        if not evaluable:
            return SectionStatus.ATTENTION

        triggered = {result.rule_id for result in evaluable if result.status == RuleStatus.TRIGGERED}
        if not triggered:
            return SectionStatus.NORMAL

        # DS001 and DS003 describe the same CFADS/debt-service weakness.
        independent_leverage_trigger = "DS002" in triggered
        cash_flow_trigger = bool(triggered & {"DS001", "DS003"})
        if independent_leverage_trigger and cash_flow_trigger:
            return SectionStatus.CRITICAL
        return SectionStatus.ATTENTION
