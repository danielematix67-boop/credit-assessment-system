from src.models.assessment import Assessment
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.services.assessment_service import AssessmentService
from src.services.behavioural_assessment_service import BehaviouralAssessmentService
from src.services.debt_sustainability_assessment_service import DebtSustainabilityAssessmentService


class CreditAssessmentCaseService:
    """Build the higher-level credit analysis case from deterministic assessments."""

    _FINANCIAL_DIMENSIONS = {
        "R001": "Revenue & Growth",
        "R002": "Profitability",
        "R003": "Profitability",
        "R004": "Financial Structure",
        "R005": "Debt Service Burden",
        "R006": "Profitability Quality",
        "R007": "Debt Service Burden",
    }

    def __init__(
        self,
        financial_assessment_service: AssessmentService,
        behavioural_assessment_service: BehaviouralAssessmentService | None = None,
        debt_sustainability_assessment_service: DebtSustainabilityAssessmentService | None = None,
    ):
        self.financial_assessment_service = financial_assessment_service
        self.behavioural_assessment_service = (
            behavioural_assessment_service or BehaviouralAssessmentService()
        )
        self.debt_sustainability_assessment_service = (
            debt_sustainability_assessment_service or DebtSustainabilityAssessmentService()
        )

    def assess(
        self,
        position: CreditPosition,
        behavioural_data: BehaviouralData | None = None,
        debt_sustainability_data: DebtSustainabilityData | None = None,
    ) -> CreditAssessmentCase:
        financial_assessment = self.financial_assessment_service.assess(position)
        behavioural_section = (
            self.behavioural_assessment_service.assess(behavioural_data)
            if behavioural_data is not None
            else self._not_evaluable_section(
                "Behavioural Analysis",
                "Behavioural banking data are not available for this case.",
            )
        )
        debt_sustainability_section = (
            self.debt_sustainability_assessment_service.assess(debt_sustainability_data)
            if debt_sustainability_data is not None
            else self._not_evaluable_section(
                "Debt Sustainability",
                "Debt-service and cash-flow data are not available for this case.",
            )
        )

        return CreditAssessmentCase(
            position=position,
            customer_profile=self._not_evaluable_section(
                "Customer Profile",
                "Customer profile data are not implemented in phase 1.",
            ),
            financial_analysis=self._financial_section(financial_assessment),
            behavioural_analysis=behavioural_section,
            debt_sustainability=debt_sustainability_section,
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
