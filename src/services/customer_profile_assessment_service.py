from pathlib import Path
from typing import Any

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.customer_profile_data import CustomerProfileData
from src.models.rule_finding import RuleFinding
from src.rules.base.severity_policy import SeverityPolicy
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class CustomerProfileAssessmentService:
    """Build the customer-profile assessment from externalized rule configuration."""

    DEFAULT_CONFIG_PATH = Path("config/customer_profile_rules.yaml")

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

    def assess(self, data: CustomerProfileData) -> AssessmentSection:
        configs = self.config_loader.load(self.config_path)
        results = [self._evaluate_rule(config, data) for config in configs]
        evaluable_results = [
            result for result in results if result.status != RuleStatus.NOT_EVALUABLE
        ]

        has_profile_data = self._has_profile_data(data)
        if not has_profile_data:
            status = SectionStatus.NOT_EVALUABLE
        elif not evaluable_results:
            status = SectionStatus.NORMAL
        else:
            status = SectionStatus(
                self.status_calculator.calculate(evaluable_results).value
            )

        findings = []
        for result in results:
            if result.status != RuleStatus.TRIGGERED:
                continue
            comment = self.comment_engine.generate(result)
            if comment is not None:
                findings.append(RuleFinding(result=result, comment=comment))
            else:
                findings.append(
                    RuleFinding(
                        result=result,
                        comment=Comment(result.rule_id, result.reason or ""),
                    )
                )

        limitations = []
        if not has_profile_data:
            limitations.append("Customer profile data are not available.")
        elif not evaluable_results:
            limitations.append("No customer-profile risk flags could be evaluated.")

        return AssessmentSection(
            name="Customer Profile",
            status=status,
            findings=findings,
            evidence=results,
            limitations=limitations,
            context={
                "company_name": data.company_name,
                "legal_form": data.legal_form,
                "sector": data.sector,
                "size_class": data.size_class,
                "geography": data.geography,
                "shareholders": list(data.shareholders),
                "management_members": list(data.management_members),
                "relationship_years": data.relationship_years,
                "business_history_years": data.business_history_years,
                "historical_facilities": list(data.historical_facilities),
                "active_ews": data.active_ews,
                "previous_restructuring": data.previous_restructuring,
            },
        )

    @staticmethod
    def _has_profile_data(data: CustomerProfileData) -> bool:
        return any(
            value not in (None, "", [])
            for value in (
                data.company_name,
                data.legal_form,
                data.sector,
                data.size_class,
                data.geography,
                data.shareholders,
                data.management_members,
                data.relationship_years,
                data.business_history_years,
                data.historical_facilities,
                data.active_ews,
                data.previous_restructuring,
            )
        )

    @staticmethod
    def _evaluate_rule(config: Any, data: CustomerProfileData) -> RuleResult:
        if not config.input_field:
            raise ValueError(
                f"Customer profile rule {config.rule_id} requires input_field"
            )

        if not hasattr(data, config.input_field):
            raise ValueError(
                f"Unknown customer profile input field: {config.input_field}"
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
        if config.severity_direction.value == "LOWER_IS_WORSE":
            triggered = value <= config.threshold
        else:
            triggered = value >= config.threshold

        severity = SeverityPolicy(
            direction=config.severity_direction,
            thresholds=config.severity_thresholds,
        ).evaluate(value) or config.severity
        status = RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED

        comparison = "at or below" if config.severity_direction.value == "LOWER_IS_WORSE" else "at or above"
        reason = (
            f"[{config.rule_id} - {config.rule_name}] {config.indicator} "
            f"is {value:g}, {comparison} the configured risk threshold."
            if triggered
            else f"[{config.rule_id} - {config.rule_name}] {config.indicator} "
            "is outside the configured risk threshold."
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
