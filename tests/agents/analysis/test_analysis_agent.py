from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.base.agent import Agent
from src.comments.comment import Comment
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_analysis_agent_implements_agent_contract():

    agent = AnalysisAgent()

    assert isinstance(agent, Agent)


def test_analysis_agent_produces_structured_analysis():

    revenue_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    ebitda_result = RuleResult(
        rule_id="R002",
        rule_name="Negative EBITDA",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-50000,
        threshold=0,
        severity=RuleSeverity.HIGH,
    )

    inventory_result = RuleResult(
        rule_id="R006",
        rule_name="EBITDA Inventory Contribution",
        category="Financial",
        status=RuleStatus.NOT_EVALUABLE,
        value=None,
        threshold=0,
        severity=RuleSeverity.MEDIUM,
    )

    findings = [
        RuleFinding(
            result=revenue_result,
            comment=Comment(
                rule_id="R001",
                text="Revenue deterioration detected.",
            ),
        ),
        RuleFinding(
            result=ebitda_result,
            comment=Comment(
                rule_id="R002",
                text="Negative EBITDA detected.",
            ),
        ),
        RuleFinding(
            result=inventory_result,
            comment=Comment(
                rule_id="R006",
                text="EBITDA Inventory Contribution could not be evaluated.",
            ),
        ),
    ]

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.CRITICAL,
        rule_results=[
            revenue_result,
            ebitda_result,
            inventory_result,
        ],
        findings=findings,
    )

    analysis = AnalysisAgent().run(assessment)

    assert isinstance(analysis, AssessmentAnalysis)
    assert analysis.position_id == "POS001"
    assert analysis.assessment_status == AssessmentStatus.CRITICAL

    assert analysis.key_findings == [
        "Revenue deterioration detected.",
        "Negative EBITDA detected.",
    ]

    assert analysis.risk_factors == [
        "Revenue deterioration detected.",
        "Negative EBITDA detected.",
    ]

    assert analysis.limitations == [
        "EBITDA Inventory Contribution",
    ]


def test_analysis_agent_uses_comment_text_for_key_findings():

    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    finding = RuleFinding(
        result=result,
        comment=Comment(
            rule_id="R001",
            text="Custom revenue deterioration comment.",
        ),
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.ATTENTION,
        rule_results=[result],
        findings=[finding],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.key_findings == [
        "Custom revenue deterioration comment.",
    ]


def test_analysis_agent_uses_comment_text_for_risk_factors():

    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    finding = RuleFinding(
        result=result,
        comment=Comment(
            rule_id="R001",
            text="Severe revenue deterioration identified.",
        ),
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.CRITICAL,
        rule_results=[result],
        findings=[finding],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.risk_factors == [
        "Severe revenue deterioration identified.",
    ]


def test_analysis_agent_does_not_depend_on_rule_ids():

    revenue_result = RuleResult(
        rule_id="CUSTOM_001",
        rule_name="Revenue Growth Deterioration",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    leverage_result = RuleResult(
        rule_id="CUSTOM_002",
        rule_name="High Leverage",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=6.0,
        threshold=5.0,
        severity=RuleSeverity.MEDIUM,
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.ATTENTION,
        rule_results=[
            revenue_result,
            leverage_result,
        ],
        findings=[
            RuleFinding(
                result=revenue_result,
                comment=Comment(
                    rule_id="CUSTOM_001",
                    text="Revenue deterioration detected.",
                ),
            ),
            RuleFinding(
                result=leverage_result,
                comment=Comment(
                    rule_id="CUSTOM_002",
                    text="High leverage detected.",
                ),
            ),
        ],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.assessment_status == AssessmentStatus.ATTENTION

    assert analysis.key_findings == [
        "Revenue deterioration detected.",
        "High leverage detected.",
    ]

    assert analysis.risk_factors == [
        "Revenue deterioration detected.",
    ]


def test_analysis_agent_ignores_not_triggered_rules():

    revenue_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    ebitda_result = RuleResult(
        rule_id="R002",
        rule_name="Positive EBITDA",
        category="Financial",
        status=RuleStatus.NOT_TRIGGERED,
        value=250000,
        threshold=0,
        severity=RuleSeverity.LOW,
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.ATTENTION,
        rule_results=[
            revenue_result,
            ebitda_result,
        ],
        findings=[
            RuleFinding(
                result=revenue_result,
                comment=Comment(
                    rule_id="R001",
                    text="Revenue deterioration detected.",
                ),
            ),
        ],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.key_findings == [
        "Revenue deterioration detected.",
    ]

    assert analysis.risk_factors == [
        "Revenue deterioration detected.",
    ]

    assert analysis.limitations == []


def test_analysis_agent_handles_normal_assessment():

    revenue_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.NOT_TRIGGERED,
        value=0.05,
        threshold=-0.10,
        severity=RuleSeverity.LOW,
    )

    ebitda_result = RuleResult(
        rule_id="R002",
        rule_name="Positive EBITDA",
        category="Financial",
        status=RuleStatus.NOT_TRIGGERED,
        value=250000,
        threshold=0,
        severity=RuleSeverity.LOW,
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.NORMAL,
        rule_results=[
            revenue_result,
            ebitda_result,
        ],
        findings=[],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.position_id == "POS001"
    assert analysis.assessment_status == AssessmentStatus.NORMAL
    assert analysis.key_findings == []
    assert analysis.risk_factors == []
    assert analysis.limitations == []


def test_analysis_agent_reports_not_evaluable_rules_as_limitations():

    revenue_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.NOT_EVALUABLE,
        value=None,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    margin_result = RuleResult(
        rule_id="R002",
        rule_name="EBITDA Margin",
        category="Financial",
        status=RuleStatus.NOT_EVALUABLE,
        value=None,
        threshold=0,
        severity=RuleSeverity.MEDIUM,
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.NORMAL,
        rule_results=[
            revenue_result,
            margin_result,
        ],
        findings=[
            RuleFinding(
                result=revenue_result,
                comment=Comment(
                    rule_id="R001",
                    text="Revenue Growth could not be evaluated.",
                ),
            ),
            RuleFinding(
                result=margin_result,
                comment=Comment(
                    rule_id="R002",
                    text="EBITDA Margin could not be evaluated.",
                ),
            ),
        ],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.key_findings == []
    assert analysis.risk_factors == []

    assert analysis.limitations == [
        "Revenue Growth",
        "EBITDA Margin",
    ]


def test_analysis_agent_selects_only_high_severity_risk_factors():

    high_result = RuleResult(
        rule_id="R001",
        rule_name="High Severity Risk",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.20,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    medium_result = RuleResult(
        rule_id="R002",
        rule_name="Medium Severity Risk",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=5.0,
        threshold=4.0,
        severity=RuleSeverity.MEDIUM,
    )

    low_result = RuleResult(
        rule_id="R003",
        rule_name="Low Severity Risk",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.5,
        severity=RuleSeverity.LOW,
    )

    assessment = Assessment(
        position_id="POS001",
        status=AssessmentStatus.CRITICAL,
        rule_results=[
            high_result,
            medium_result,
            low_result,
        ],
        findings=[
            RuleFinding(
                result=high_result,
                comment=Comment(
                    rule_id="R001",
                    text="High severity risk detected.",
                ),
            ),
            RuleFinding(
                result=medium_result,
                comment=Comment(
                    rule_id="R002",
                    text="Medium severity risk detected.",
                ),
            ),
            RuleFinding(
                result=low_result,
                comment=Comment(
                    rule_id="R003",
                    text="Low severity risk detected.",
                ),
            ),
        ],
    )

    analysis = AnalysisAgent().run(assessment)

    assert analysis.key_findings == [
        "High severity risk detected.",
        "Medium severity risk detected.",
        "Low severity risk detected.",
    ]

    assert analysis.risk_factors == [
        "High severity risk detected.",
    ]