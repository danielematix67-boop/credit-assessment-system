from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition

def test_assessment_workflow_executes_all_stages(
    assessment_service,
):

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=AnalysisAgent(),
        reporting_agent=ReportingAgent(),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    assert result.assessment.position_id == "POS001"
    assert result.analysis.position_id == "POS001"
    assert result.report.position_id == "POS001"

    assert result.report.assessment_status == (
        result.assessment.status
    )