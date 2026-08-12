from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.orchestration.orchestrator import AssessmentOrchestrator


def create_default_orchestrator() -> AssessmentOrchestrator:
    workflow = create_default_assessment_workflow()

    return AssessmentOrchestrator(
        workflow=workflow,
    )