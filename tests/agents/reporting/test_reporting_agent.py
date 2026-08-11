from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.report import Report


def test_reporting_agent_preserves_deterministic_assessment(
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

    assessment = assessment_service.assess(position)

    agent = ReportingAgent()
    report = agent.run(assessment)

    # The reporting layer must preserve the
    # deterministic assessment identity and status.
    assert report.position_id == assessment.position_id
    assert report.assessment_status == assessment.status

    # Findings must correspond exactly to triggered rules.
    expected_findings = [
        result.rule_name
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    ]

    assert report.findings == expected_findings

    # Every non-evaluable rule must be represented
    # as a reporting limitation.
    expected_limitations = [
        result.rule_name
        for result in assessment.rule_results
        if result.status == RuleStatus.NOT_EVALUABLE
    ]

    assert len(report.limitations) == len(expected_limitations)

    # The reporting agent must not create findings
    # for rules that were not triggered.
    not_triggered_rule_names = {
        result.rule_name
        for result in assessment.rule_results
        if result.status == RuleStatus.NOT_TRIGGERED
    }

    assert not_triggered_rule_names.isdisjoint(
        set(report.findings)
    )


def test_reporting_agent_generates_summary_from_assessment_status(
    assessment_service,
):
    scenarios = [
        (
            CreditPosition(
                position_id="POS001",
                revenue_growth=0.05,
                ebitda=250000,
                profit_loss=50000,
                ebitda_margin=0.10,
                pfn_to_ebitda=3.5,
                interest_expense=40000,
            ),
            AssessmentStatus.NORMAL,
            "normal",
        ),
        (
            CreditPosition(
                position_id="POS002",
                revenue_growth=0.05,
                ebitda=250000,
                profit_loss=50000,
                ebitda_margin=0.10,
                pfn_to_ebitda=6.0,
                interest_expense=40000,
            ),
            AssessmentStatus.ATTENTION,
            "attention",
        ),
        (
            CreditPosition(
                position_id="POS003",
                revenue_growth=-0.15,
                ebitda=-50000,
                profit_loss=-50000,
                ebitda_margin=-0.05,
                pfn_to_ebitda=6.0,
                interest_expense=40000,
            ),
            AssessmentStatus.CRITICAL,
            "critical",
        ),
    ]

    agent = ReportingAgent()

    for position, expected_status, expected_keyword in scenarios:
        assessment = assessment_service.assess(position)

        assert assessment.status == expected_status

        report = agent.run(assessment)

        assert report.assessment_status == expected_status
        assert expected_keyword in report.executive_summary.lower()


def test_reporting_agent_does_not_depend_on_rule_ids(
    assessment_service,
):
    position = CreditPosition(
        position_id="POS004",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    assessment = assessment_service.assess(position)

    agent = ReportingAgent()
    report = agent.run(assessment)

    triggered_rule_names = [
        result.rule_name
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    ]

    assert report.findings == triggered_rule_names


def test_reporting_agent_implements_agent_contract():
    agent = ReportingAgent()

    assert isinstance(agent, Agent)

    assert isinstance(agent, Agent)

    assert agent.run.__annotations__["assessment"] is Assessment
    assert agent.run.__annotations__["return"] is Report