from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.base.agent import Agent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report, ReportFindingGroup
from src.rules.base.severity import RuleSeverity


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
        reporting_agent=ReportingAgent(
            report_generator=DeterministicReportGenerator(),
        ),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    assert result.assessment.position_id == "POS001"
    assert result.analysis.position_id == "POS001"
    assert result.report.position_id == "POS001"

    assert result.report.assessment_status == (
        result.assessment.status
    )


def test_assessment_workflow_accepts_agent_contracts(
    assessment_service,
):
    class TestAnalysisAgent(
        Agent[Assessment, AssessmentAnalysis]
    ):
        def run(
            self,
            assessment: Assessment,
        ) -> AssessmentAnalysis:
            return AssessmentAnalysis(
                position_id=assessment.position_id,
                assessment_status=assessment.status,
                key_findings=[
                    AnalysisFinding(
                        rule_id="TEST_RULE",
                        category="profitability",
                        severity=RuleSeverity.HIGH,
                        text="Test finding",
                    ),
                ],
                risk_factors=[
                    AnalysisFinding(
                        rule_id="TEST_RULE",
                        category="profitability",
                        severity=RuleSeverity.HIGH,
                        text="Test risk",
                    ),
                ],
                limitations=[],
            )

    class TestReportingAgent(
        Agent[AssessmentAnalysis, Report]
    ):
        def run(
            self,
            analysis: AssessmentAnalysis,
        ) -> Report:
            categories = {}

            for finding in analysis.key_findings:
                categories.setdefault(
                    finding.category,
                    [],
                ).append(finding)

            findings_by_category = [
                ReportFindingGroup(
                    category=category,
                    findings=findings,
                )
                for category, findings in categories.items()
            ]

            return Report(
                position_id=analysis.position_id,
                assessment_status=analysis.assessment_status,
                executive_summary="Test summary",
                findings_by_category=findings_by_category,
                limitations=analysis.limitations,
            )

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
        analysis_agent=TestAnalysisAgent(),
        reporting_agent=TestReportingAgent(),
    )

    result = workflow.run(position)

    assert isinstance(result, AssessmentWorkflowResult)

    # Analysis findings
    assert len(result.analysis.key_findings) == 1

    finding = result.analysis.key_findings[0]

    assert isinstance(finding, AnalysisFinding)
    assert finding.rule_id == "TEST_RULE"
    assert finding.category == "profitability"
    assert finding.severity == RuleSeverity.HIGH
    assert finding.text == "Test finding"

    # Risk factors
    assert len(result.analysis.risk_factors) == 1

    risk_factor = result.analysis.risk_factors[0]

    assert isinstance(risk_factor, AnalysisFinding)
    assert risk_factor.rule_id == "TEST_RULE"
    assert risk_factor.category == "profitability"
    assert risk_factor.severity == RuleSeverity.HIGH
    assert risk_factor.text == "Test risk"

    # Report
    assert result.report.executive_summary == "Test summary"

    assert result.report.findings_by_category == [
        ReportFindingGroup(
            category="profitability",
            findings=[
                finding,
            ],
        ),
    ]

    assert result.report.limitations == []
