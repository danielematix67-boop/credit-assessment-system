from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_analysis_agent_implements_agent_contract():

    agent = AnalysisAgent()

    assert isinstance(agent, Agent)


def test_analysis_agent_produces_structured_analysis():

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.CRITICAL,
        rule_results=[
            RuleResult(
                rule_id="R001",
                rule_name="Revenue Growth",
                category="Financial",
                status=RuleStatus.TRIGGERED,
                value=-0.15,
                threshold=-0.10,
                severity=None,
            ),
            RuleResult(
                rule_id="R002",
                rule_name="Negative EBITDA",
                category="Financial",
                status=RuleStatus.TRIGGERED,
                value=-50000,
                threshold=0,
                severity=None,
            ),
            RuleResult(
                rule_id="R006",
                rule_name="EBITDA Inventory Contribution",
                category="Financial",
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=0,
                severity=None,
            ),
        ],
        comments=[],
    )

    agent = AnalysisAgent()

    analysis = agent.run(assessment)

    assert isinstance(analysis, AssessmentAnalysis)
    assert analysis.position_id == "POS001"
    assert analysis.assessment_status == AssessmentStatus.CRITICAL

    assert analysis.key_findings == [
        "Revenue Growth",
        "Negative EBITDA",
    ]

    assert analysis.risk_factors == [
        "Revenue Growth",
        "Negative EBITDA",
    ]

    assert analysis.limitations == [
        "EBITDA Inventory Contribution",
    ]


def test_analysis_agent_does_not_depend_on_rule_ids():

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.ATTENTION,
        rule_results=[
            RuleResult(
                rule_id="CUSTOM_001",
                rule_name="Revenue Growth Deterioration",
                category="Financial",
                status=RuleStatus.TRIGGERED,
                value=-0.15,
                threshold=-0.10,
                severity=None,
            ),
            RuleResult(
                rule_id="CUSTOM_002",
                rule_name="High Leverage",
                category="Financial",
                status=RuleStatus.TRIGGERED,
                value=6.0,
                threshold=5.0,
                severity=None,
            ),
        ],
        comments=[],
    )

    agent = AnalysisAgent()

    analysis = agent.run(assessment)

    assert analysis.assessment_status == AssessmentStatus.ATTENTION

    assert analysis.key_findings == [
        "Revenue Growth Deterioration",
        "High Leverage",
    ]

    assert analysis.risk_factors == [
        "Revenue Growth Deterioration",
        "High Leverage",
    ]

def test_analysis_agent_ignores_not_triggered_rules():

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.ATTENTION,
        rule_results=[
            RuleResult(
                rule_id="R001",
                rule_name="Revenue Growth",
                category="Financial",
                status=RuleStatus.TRIGGERED,
                value=-0.15,
                threshold=-0.10,
                severity=None,
            ),
            RuleResult(
                rule_id="R002",
                rule_name="Positive EBITDA",
                category="Financial",
                status=RuleStatus.NOT_TRIGGERED,
                value=250000,
                threshold=0,
                severity=None,
            ),
        ],
        comments=[],
    )

    agent = AnalysisAgent()

    analysis = agent.run(assessment)

    assert analysis.key_findings == [
        "Revenue Growth",
    ]

    assert analysis.risk_factors == [
        "Revenue Growth",
    ]

    assert analysis.limitations == []

def test_analysis_agent_handles_normal_assessment():

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.NORMAL,
        rule_results=[
            RuleResult(
                rule_id="R001",
                rule_name="Revenue Growth",
                category="Financial",
                status=RuleStatus.NOT_TRIGGERED,
                value=0.05,
                threshold=-0.10,
                severity=None,
            ),
            RuleResult(
                rule_id="R002",
                rule_name="Positive EBITDA",
                category="Financial",
                status=RuleStatus.NOT_TRIGGERED,
                value=250000,
                threshold=0,
                severity=None,
            ),
        ],
        comments=[],
    )

    agent = AnalysisAgent()

    analysis = agent.run(assessment)

    assert analysis.position_id == "POS001"
    assert analysis.assessment_status == AssessmentStatus.NORMAL
    assert analysis.key_findings == []
    assert analysis.risk_factors == []
    assert analysis.limitations == []

def test_analysis_agent_reports_not_evaluable_rules_as_limitations():

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.NORMAL,
        rule_results=[
            RuleResult(
                rule_id="R001",
                rule_name="Revenue Growth",
                category="Financial",
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=-0.10,
                severity=None,
            ),
            RuleResult(
                rule_id="R002",
                rule_name="EBITDA Margin",
                category="Financial",
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=0,
                severity=None,
            ),
        ],
        comments=[],
    )

    agent = AnalysisAgent()

    analysis = agent.run(assessment)

    assert analysis.key_findings == []
    assert analysis.risk_factors == []

    assert analysis.limitations == [
        "Revenue Growth",
        "EBITDA Margin",
    ]