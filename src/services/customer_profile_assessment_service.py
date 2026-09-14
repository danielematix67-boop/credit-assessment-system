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
                "legal_form": data.legal_form,
                "sector": data.sector,
                "size_class": data.size_class,
                "geography": data.geography,
                "shareholders": list(data.shareholders),
                "management_members": list(data.management_members),
                "relationship_years": data.relationship_years,
                "business_history_years": data.business_history_years,
                "historical_facilities": list(data.historical_facilities),
                "ews_score_class": (
                    data.ews_score_class.value if data.ews_score_class else None
                ),
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
                data.ews_score_class,
                data.previous_restructuring,
            )
        )
