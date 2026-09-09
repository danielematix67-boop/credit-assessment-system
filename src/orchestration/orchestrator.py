from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report


class AssessmentOrchestrator:
    def __init__(
        self,
        workflow: AssessmentWorkflow,
    ):
        self.workflow = workflow

    def run(self, position: CreditPosition) -> Report:
        result: AssessmentWorkflowResult = self.workflow.run(position)

        return result.report
