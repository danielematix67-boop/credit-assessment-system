from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.financial_assessment import FinancialAssessment
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_service import AssessmentService
from src.services.behavioural_assessment_service import BehaviouralAssessmentService
from src.services.customer_profile_assessment_service import CustomerProfileAssessmentService
from src.services.debt_sustainability_assessment_service import DebtSustainabilityAssessmentService
from src.services.final_assessment_service import FinalAssessmentService


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
        customer_profile_assessment_service: CustomerProfileAssessmentService | None = None,
        final_assessment_service: FinalAssessmentService | None = None,
    ) -> None:
        self.financial_assessment_service = financial_assessment_service
        self.behavioural_assessment_service = behavioural_assessment_service or BehaviouralAssessmentService()
        self.debt_sustainability_assessment_service = (
            debt_sustainability_assessment_service or DebtSustainabilityAssessmentService()
        )
        self.customer_profile_assessment_service = (
            customer_profile_assessment_service or CustomerProfileAssessmentService()
        )
        self.final_assessment_service = final_assessment_service or FinalAssessmentService()

    def assess(
        self,
        position: CreditPosition,
        behavioural_data: BehaviouralData | None = None,
        debt_sustainability_data: DebtSustainabilityData | None = None,
        customer_profile_data: CustomerProfileData | None = None,
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
        customer_profile_section = (
            self.customer_profile_assessment_service.assess(customer_profile_data)
            if customer_profile_data is not None
            else self._not_evaluable_section(
                "Customer Profile",
                "Customer profile data are not available for this case.",
            )
        )

        case = CreditAssessmentCase(
            position=position,
            customer_profile=customer_profile_section,
            financial_analysis=self._financial_section(financial_assessment),
            behavioural_analysis=behavioural_section,
            debt_sustainability=debt_sustainability_section,
        )
        final_assessment = self.final_assessment_service.assess(case)
        return CreditAssessmentCase(
            position=case.position,
            customer_profile=case.customer_profile,
            financial_analysis=case.financial_analysis,
            behavioural_analysis=case.behavioural_analysis,
            debt_sustainability=case.debt_sustainability,
            final_assessment=final_assessment,
        )

    @classmethod
    def _financial_section(cls, assessment: FinancialAssessment) -> AssessmentSection:
        dimensions: dict[str, list[RuleResult]] = {}
        for result in assessment.rule_results:
            dimension = cls._FINANCIAL_DIMENSIONS.get(result.rule_id, "Other Financial Indicators")
            dimensions.setdefault(dimension, []).append(result)

        all_not_evaluable = bool(assessment.rule_results) and all(
            result.status == RuleStatus.NOT_EVALUABLE for result in assessment.rule_results
        )
        status = SectionStatus.NOT_EVALUABLE if all_not_evaluable else SectionStatus(assessment.status.value)
        limitations = ["Financial indicators are not available for this case."] if all_not_evaluable else []

        return AssessmentSection(
            name="Financial Analysis",
            status=status,
            findings=assessment.findings,
            evidence=assessment.rule_results,
            limitations=limitations,
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
