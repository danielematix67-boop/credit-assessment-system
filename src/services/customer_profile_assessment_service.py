from pathlib import Path
from typing import cast

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.customer_profile_data import CustomerProfileData
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.rules.base.status import RuleStatus
from src.rules.registry import build_rules
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class CustomerProfileAssessmentService:
    """Build customer-profile assessment using the shared Rule implementation."""

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
        results = [
            rule.evaluate(cast(CreditPosition, data)) for rule in build_rules(configs)
        ]
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
            findings.append(
                RuleFinding(
                    result=result,
                    comment=comment or Comment(result.rule_id, result.reason or ""),
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
                "counterparty_type": data.counterparty_type,
                "legal_form": data.legal_form,
                "sector": data.sector,
                "size_class": data.size_class,
                "geography": data.geography,
                "business_history_years": data.business_history_years,
                "operations": list(data.operations),
                "forborne_non_performing_exit": data.forborne_non_performing_exit,
                "past_due_count": data.past_due_count,
                "cure_period_days": data.cure_period_days,
                "monitoring_period_days": data.monitoring_period_days,
                "probation_period_days": data.probation_period_days,
                "minimum_regulatory_risk_grade": data.minimum_regulatory_risk_grade,
                "previous_risk_grade": data.previous_risk_grade,
                "risk_grade_change": data.risk_grade_change,
                "ews_score_class": (
                    data.ews_score_class.value if data.ews_score_class else None
                ),
                "ews_score_notching": data.ews_score_notching,
                "ews_score_variation": data.ews_score_variation,
                "active_ewis": list(data.active_ewis),
                "rating": data.rating,
                "rating_notching": data.rating_notching,
                "rating_influential_factors": list(data.rating_influential_factors),
                "rating_elementary_modules": list(data.rating_elementary_modules),
                "pd": data.pd,
                "risk_group_interdependence": data.risk_group_interdependence,
                "risk_group_independence": data.risk_group_independence,
                "shareholders": list(data.shareholders),
                "shareholder_roles": list(data.shareholder_roles),
                "management_members": list(data.management_members),
                "generational_transition": data.generational_transition,
                "employment_contract_type": data.employment_contract_type,
                "economic_family_context": data.economic_family_context,
                "relationship_years": data.relationship_years,
                "historical_facilities": list(data.historical_facilities),
                "previous_restructuring": data.previous_restructuring,
                "forborne": data.forborne,
                "protests": list(data.protests),
                "bankruptcies": list(data.bankruptcies),
                "litigation": list(data.litigation),
                "significant_historical_events": list(data.significant_historical_events),
            },
        )

    @staticmethod
    def _has_profile_data(data: CustomerProfileData) -> bool:
        return any(
            value not in (None, "", [])
            for value in (
                data.company_name,
                data.counterparty_type,
                data.legal_form,
                data.sector,
                data.size_class,
                data.geography,
                data.business_history_years,
                data.operations,
                data.forborne_non_performing_exit,
                data.past_due_count,
                data.cure_period_days,
                data.monitoring_period_days,
                data.probation_period_days,
                data.minimum_regulatory_risk_grade,
                data.previous_risk_grade,
                data.risk_grade_change,
                data.ews_score_class,
                data.ews_score_notching,
                data.ews_score_variation,
                data.active_ewis,
                data.rating,
                data.rating_notching,
                data.rating_influential_factors,
                data.rating_elementary_modules,
                data.pd,
                data.risk_group_interdependence,
                data.risk_group_independence,
                data.shareholders,
                data.shareholder_roles,
                data.management_members,
                data.generational_transition,
                data.employment_contract_type,
                data.economic_family_context,
                data.relationship_years,
                data.historical_facilities,
                data.previous_restructuring,
                data.forborne,
                data.protests,
                data.bankruptcies,
                data.litigation,
                data.significant_historical_events,
            )
        )
