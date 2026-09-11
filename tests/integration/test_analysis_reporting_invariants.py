from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.final_assessment import FinalAssessment
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def _finding(
    rule_id: str,
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    text: str = "Synthetic risk triggered.",
) -> RuleFinding:
    return RuleFinding(
        result=RuleResult(
            rule_id=rule_id,
            rule_name=f"{rule_id} risk",
            category="Financial Analysis",
            status=RuleStatus.TRIGGERED,
            value=1.0,
            threshold=0.5,
            severity=severity,
            indicator=rule_id,
            direction=SeverityDirection.HIGHER_IS_WORSE,
        ),
        comment=type("CommentStub", (), {"text": text})(),
    )


def _case() -> CreditAssessmentCase:
    position = CreditPosition(position_id="INVARIANT-001")
    financial = AssessmentSection(
        name="Financial Analysis",
        status=SectionStatus.ATTENTION,
        findings=[_finding("R001", RuleSeverity.HIGH)],
        evidence=[],
        limitations=["Financial limitation."],
    )
    return CreditAssessmentCase(
        position=position,
        customer_profile=AssessmentSection(
            name="Customer Profile",
            status=SectionStatus.NOT_EVALUABLE,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        financial_analysis=financial,
        behavioural_analysis=AssessmentSection(
            name="Behavioural Analysis",
            status=SectionStatus.NORMAL,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        debt_sustainability=AssessmentSection(
            name="Debt Sustainability",
            status=SectionStatus.NORMAL,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        final_assessment=FinalAssessment(
            status=SectionStatus.ATTENTION,
            evaluated_sections=1,
            risk_sections=["Financial Analysis"],
            limitations=["Final limitation."],
        ),
    )


def test_analysis_agent_preserves_deterministic_final_status_and_evidence() -> None:
    analysis = CaseAnalysisAgent().run(_case())

    assert analysis.assessment_status == AssessmentStatus.ATTENTION
    assert [finding.rule_id for finding in analysis.key_findings] == ["R001"]
    assert [finding.rule_id for finding in analysis.risk_factors] == ["R001"]
    assert [finding.text for finding in analysis.limitations] == [
        "Financial limitation.",
        "Final limitation.",
    ]


def test_analysis_agent_does_not_recalculate_status_when_case_status_changes() -> None:
    case = _case()
    case_with_changed_final_status = CreditAssessmentCase(
        position=case.position,
        customer_profile=case.customer_profile,
        financial_analysis=case.financial_analysis,
        behavioural_analysis=case.behavioural_analysis,
        debt_sustainability=case.debt_sustainability,
        final_assessment=FinalAssessment(
            status=SectionStatus.CRITICAL,
            evaluated_sections=1,
            risk_sections=["Financial Analysis"],
        ),
    )

    analysis = CaseAnalysisAgent().run(case_with_changed_final_status)

    assert analysis.assessment_status == AssessmentStatus.CRITICAL
    assert analysis.key_findings[0].rule_id == "R001"


def test_deterministic_report_reuses_analysis_status_findings_and_limitations() -> None:
    analysis = AssessmentAnalysis(
        position_id="INVARIANT-002",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            AnalysisFinding(
                rule_id="R004",
                category="Financial Structure",
                severity=RuleSeverity.HIGH,
                text="Leverage is elevated.",
            )
        ],
        risk_factors=[],
        limitations=[
            AnalysisFinding(
                rule_id="FINAL",
                category="Final Assessment",
                severity=RuleSeverity.MEDIUM,
                text="Synthetic limitation.",
            )
        ],
    )

    report = DeterministicReportGenerator().generate(analysis)

    assert report.assessment_status is analysis.assessment_status
    assert report.limitations is analysis.limitations
    assert report.findings_by_category[0].findings is analysis.key_findings


def test_reporting_fallback_reuses_exact_same_analysis_without_reassessment() -> None:
    class FailingGenerator:
        def generate(self, analysis: AssessmentAnalysis) -> None:
            raise RuntimeError("synthetic generation failure")

    class CapturingGenerator:
        def __init__(self) -> None:
            self.received: AssessmentAnalysis | None = None

        def generate(self, analysis: AssessmentAnalysis):
            self.received = analysis
            return DeterministicReportGenerator().generate(analysis)

    analysis = AssessmentAnalysis(
        position_id="INVARIANT-003",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )
    fallback = CapturingGenerator()
    report = ReportingAgent(
        report_generator=FailingGenerator(),
        fallback_generator=fallback,
    ).run(analysis)

    assert fallback.received is analysis
    assert report.assessment_status is analysis.assessment_status
