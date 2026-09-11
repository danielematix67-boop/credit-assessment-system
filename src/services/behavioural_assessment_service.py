from pathlib import Path
from typing import Any

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.models.rule_finding import RuleFinding
from src.rules.base.severity_policy import SeverityPolicy
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class BehaviouralAssessmentService:
    """Build the behavioural assessment from externalized rule configuration."""

    DEFAULT_CONFIG_PATH = Path("config/behavioural_analysis_rules.yaml")

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

    def assess(self, data: BehaviouralData) -> AssessmentSection:
        configs = self.config_loader.load(self.config_path)
        results = [self._evaluate_rule(config, data) for config in configs]
        findings = []

        for result in results:
            if result.status != RuleStatus.TRIGGERED:
                continue
            comment = self.comment_engine.generate(result)
            if comment is None:
                comment = Comment(result.rule_id, result.reason or "")
            findings.append(RuleFinding(result=result, comment=comment))

        limitations = []
        if all(result.status == RuleStatus.NOT_EVALUABLE for result in results):
            limitations.append("Behavioural banking indicators are not available.")

        return AssessmentSection(
            name="Behavioural Analysis",
            status=SectionStatus(self.status_calculator.calculate(results).value),
            findings=findings,
            evidence=results,
            limitations=limitations,
        )

    @staticmethod
    def _evaluate_rule(config: Any, data: BehaviouralData) -> RuleResult:
        if not config.input_field:
            raise ValueError(
                f"Behavioural rule {config.rule_id} requires input_field"
            )
        if not hasattr(data, config.input_field):
            raise ValueError(
                f"Unknown behavioural input field: {config.input_field}"
            )

        raw_value = getattr(data, config.input_field)
        if raw_value is None:
            return RuleResult(
                rule_id=config.rule_id,
                rule_name=config.rule_name,
                category=config.category,
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=config.threshold,
                severity=config.severity,
                reason=(
                    f"[{config.rule_id} - {config.rule_name}] "
                    f"{config.indicator} is not available."
                ),
                indicator=config.indicator,
                direction=config.severity_direction,
                comment_template=config.comment_template,
            )

        value = float(raw_value)
        triggered = BehaviouralAssessmentService._matches_operator(
            value, config.threshold, config.trigger_operator
        )
        status = RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED
        severity = SeverityPolicy(
            direction=config.severity_direction,
            thresholds=config.severity_thresholds,
        ).evaluate(value) or config.severity
        reason = BehaviouralAssessmentService._build_reason(
            config.indicator,
            value,
            config.threshold,
            config.trigger_operator,
            status,
        )

        return RuleResult(
            rule_id=config.rule_id,
            rule_name=config.rule_name,
            category=config.category,
            status=status,
            value=value,
            threshold=config.threshold,
            severity=severity,
            reason=f"[{config.rule_id} - {config.rule_name}] {reason}",
            indicator=config.indicator,
            direction=config.severity_direction,
            comment_template=config.comment_template,
        )

    @staticmethod
    def _build_reason(
        indicator: str,
        value: float,
        threshold: float,
        operator: str,
        status: RuleStatus,
    ) -> str:
        if status == RuleStatus.TRIGGERED:
            relation = {
                "GT": "above",
                "GTE": "at or above",
                "LT": "below",
                "LTE": "at or below",
            }[operator]
            return (
                f"{indicator} is {value:.2f}, {relation} the configured "
                f"threshold of {threshold:.2f}."
            )

        relation = {
            "GT": "at or below",
            "GTE": "below",
            "LT": "at or above",
            "LTE": "above",
        }[operator]
        return (
            f"{indicator} is {value:.2f}, {relation} the configured "
            f"threshold of {threshold:.2f}."
        )

    @staticmethod
    def _matches_operator(value: float, threshold: float, operator: str) -> bool:
        if operator == "GT":
            return value > threshold
        if operator == "GTE":
            return value >= threshold
        if operator == "LT":
            return value < threshold
        if operator == "LTE":
            return value <= threshold
        raise ValueError(f"Unsupported trigger operator: {operator}")
