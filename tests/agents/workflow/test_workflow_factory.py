import pytest

from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.llm.mock_client import MockLLMClient
from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus


def test_default_workflow_factory_creates_valid_workflow():

    workflow = create_default_assessment_workflow()

    assert isinstance(
        workflow,
        AssessmentWorkflow,
    )

    assert isinstance(
        workflow.analysis_agent,
        AnalysisAgent,
    )

    assert isinstance(
        workflow.reporting_agent,
        ReportingAgent,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        DeterministicReportGenerator,
    )


def test_workflow_factory_can_create_llm_workflow():

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=MockLLMClient(),
    )

    assert isinstance(
        workflow,
        AssessmentWorkflow,
    )

    assert isinstance(
        workflow.analysis_agent,
        AnalysisAgent,
    )

    assert isinstance(
        workflow.reporting_agent,
        ReportingAgent,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        LLMReportGenerator,
    )


def test_workflow_factory_requires_llm_client_when_llm_enabled():

    with pytest.raises(
        ValueError,
        match="llm_client is required when use_llm=True",
    ):
        create_default_assessment_workflow(
            use_llm=True,
            llm_client=None,
        )


def test_default_workflow_factory_propagates_rule_comments():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = create_default_assessment_workflow(
        use_llm=False,
    )

    result = workflow.run(position)

    assessment_comments = [
        finding.comment.text
        for finding in result.assessment.findings
        if finding.result.status == RuleStatus.TRIGGERED
    ]

    assert assessment_comments

    assert result.analysis.key_findings == (
        assessment_comments
    )

    assert result.report.findings == (
        assessment_comments
    )


def test_workflow_factory_preserves_comments_with_llm():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=MockLLMClient(
            response="CRITICAL assessment identified.",
        ),
    )

    result = workflow.run(position)

    assessment_comments = [
        finding.comment.text
        for finding in result.assessment.findings
        if finding.result.status == RuleStatus.TRIGGERED
    ]

    assert result.assessment.status == (
        AssessmentStatus.CRITICAL
    )

    assert result.analysis.key_findings == (
        assessment_comments
    )

    assert result.report.findings == (
        assessment_comments
    )

    assert result.report.assessment_status == (
        result.assessment.status
    )