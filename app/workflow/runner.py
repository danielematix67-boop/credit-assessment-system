from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.position import CreditPosition


def run_assessment(
    workflow: AssessmentWorkflow,
    position: CreditPosition,
):
    """
    Execute the assessment workflow for a credit position.

    Streamlit is responsible only for presentation and user interaction.
    Workflow execution remains outside the UI layer.
    """

    return workflow.run(position)
