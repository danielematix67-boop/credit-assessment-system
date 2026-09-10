from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.customer_profile_data import CustomerProfileData
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.customer_profile_assessment_service import CustomerProfileAssessmentService


def _section(name: str, status: SectionStatus, finding: RuleFinding | None = None) -> AssessmentSection:
    return AssessmentSection(name=name, status=status, findings=[finding] if finding else [], evidence=[], limitations=[])


def test_case_analysis_agent_maps_final_status_and_findings() -> None:
    position = CreditPosition(position_id="TEST-001")
    finding = RuleFinding(
        result=RuleResult(
            rule_id="X001", rule_name="Synthetic risk", category="Behavioural Analysis",
            status=RuleStatus.TRIGGERED, value=1.0, threshold=0.5,
            severity=RuleSeverity.HIGH, indicator="Synthetic", direction=SeverityDirection.HIGHER_IS_WORSE,
        ),
        comment=type("CommentStub", (), {"text": "Synthetic risk triggered."})(),
    )
    case = CreditAssessmentCase(
        position=position,
        customer_profile=_section("Customer Profile", SectionStatus.NOT_EVALUABLE),
        financial_analysis=_section("Financial Analysis", SectionStatus.NORMAL),
        behavioural_analysis=_section("Behavioural Analysis", SectionStatus.ATTENTION, finding),
        debt_sustainability=_section("Debt Sustainability", SectionStatus.NORMAL),
    )
    analysis = CaseAnalysisAgent().run(case)
    assert analysis.assessment_status == AssessmentStatus.ATTENTION
    assert analysis.key_findings[0].rule_id == "X001"
    assert analysis.risk_factors[0].rule_id == "X001"


def test_case_analysis_agent_includes_customer_profile_context() -> None:
    position = CreditPosition(position_id="TEST-002")
    profile = CustomerProfileAssessmentService().assess(
        CustomerProfileData(company_name="Synthetic Co.", sector="Manufacturing", relationship_years=7)
    )
    case = CreditAssessmentCase(
        position=position,
        customer_profile=profile,
        financial_analysis=_section("Financial Analysis", SectionStatus.NORMAL),
        behavioural_analysis=_section("Behavioural Analysis", SectionStatus.NOT_EVALUABLE),
        debt_sustainability=_section("Debt Sustainability", SectionStatus.NOT_EVALUABLE),
    )
    analysis = CaseAnalysisAgent().run(case)
    assert analysis.assessment_status == AssessmentStatus.NORMAL
    assert analysis.key_findings[0].category == "Customer Profile"
    assert "Synthetic Co." in analysis.key_findings[0].text
