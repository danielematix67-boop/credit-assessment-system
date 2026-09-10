from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.behavioural_data import BehaviouralData
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition


def run_assessment(
    workflow: AssessmentWorkflow,
    position: CreditPosition,
    *,
    behavioural_data: BehaviouralData | None = None,
    debt_sustainability_data: DebtSustainabilityData | None = None,
    customer_profile_data: CustomerProfileData | None = None,
):
    """Execute the assessment workflow for a credit position."""

    return workflow.run(
        position,
        behavioural_data=behavioural_data,
        debt_sustainability_data=debt_sustainability_data,
        customer_profile_data=customer_profile_data,
    )
