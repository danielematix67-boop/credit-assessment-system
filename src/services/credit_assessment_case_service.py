from src.models.assessment import Assessment
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.services.assessment_service import AssessmentService


class CreditAssessmentCaseService:
    """Build the higher-level credit analysis case from deterministic assessments.

    Phase 1 intentionally implements only the financial-analysis section. The
    remaining macro-areas are explicit NOT_EVALUABLE placeholders so that future
    functionality can be added without changing the case contract.
    """

    _FINANCIAL_DIMENSIONS = {
        "R001": "Revenue & Growth",
        "R002": "Profitability",
        "R003": "Profitability",
        "R004": "Financial Structure",
        "R005": "Debt Service Burden",
        "R006": "Profitability Quality",
        "R007": "Debt Service Burden",
    }

    def __init__(self, financial_assessment_service: AssessmentService):
        self.financial_assessment_service = financial_assessment_service

    def assess(self, position: CreditPosition) -> CreditAssessmentCase:
        financial_assessment = self.financial_assessment_service.assess(position)

        return CreditAssessmentCase(
            position=position,
            customer_profile=self._not_evaluable_section(
                "Customer Profile",
                "Customer profile data are not implemented in phase 1.",
            ),
            financial_analysis=self._financial_section(financial_assessment),
            behavioural_analysis=self._not_evaluable_section(
                "Behavioural Analysis",
                "Behavioural banking data are not implemented in phase 1.",
            ),
            debt_sustainability=self._not_evaluable_section(
                "Debt Sustainability",
                "Debt-service and cash-flow analysis are not implemented in phase 1.",
            ),
        )

    @classmethod
    def _financial_section(cls, assessment: Assessment) -> AssessmentSection:
        dimensions: dict[str, list[RuleResult]] = {}
        for result in assessment.rule_results:
            dimension = cls._FINANCIAL_DIMENSIONS.get(
                result.rule_id,
                "Other Financial Indicators",
            )
            dimensions.setdefault(dimension, []).append(result)

        return AssessmentSection(
            name="Financial Analysis",
            status=SectionStatus(assessment.status.value),
            findings=assessment.findings,
            evidence=assessment.rule_results,
            limitations=[],
            dimensions=dimensions,
        )

    @staticmethod
    def _not_evaluable_section(name: str, limitation: str) -> AssessmentSection:
        return AssessmentSection(
            name=name,
            status=SectionStatus.NOT_EVALUABLE,
            findings=[],
            evidence=[],
            limitations=[limitation],
        )
