from pathlib import Path

from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.engine.rule_engine import RuleEngine
from src.models.assessment_section import SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.discovery import discover_rules
from src.services.assessment_service import AssessmentService
from src.services.assessment_status_calculator import AssessmentStatusCalculator
from src.services.behavioural_assessment_service import BehaviouralAssessmentService
from src.services.credit_assessment_case_service import CreditAssessmentCaseService
from src.services.debt_sustainability_assessment_service import (
    DebtSustainabilityAssessmentService,
)
from src.services.final_assessment_service import FinalAssessmentService
from src.services.position_validator import CreditPositionValidator

RULES_CONFIG_PATH = Path("config/financial_analysis_rules.yaml")


def _case_service() -> CreditAssessmentCaseService:
    discover_rules()
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    rules = [Rule.get_registered_rule(config.rule_id)(config) for config in configs]
    assessment_service = AssessmentService(
        rule_engine=RuleEngine(rules),
        comment_engine=CommentEngine(),
        status_calculator=AssessmentStatusCalculator(),
        position_validator=CreditPositionValidator(),
    )
    return CreditAssessmentCaseService(
        assessment_service,
        behavioural_assessment_service=BehaviouralAssessmentService(),
        debt_sustainability_assessment_service=DebtSustainabilityAssessmentService(),
        final_assessment_service=FinalAssessmentService(),
    )


def _position(**overrides: float) -> CreditPosition:
    values = {
        "revenue_growth": 0.05,
        "ebitda": 100.0,
        "ebitda_margin": 0.10,
        "nfp_to_ebitda": 4.0,
        "interest_expense": 50.0,
        "change_in_finished_goods_inventory": 20.0,
    }
    values.update(overrides)
    return CreditPosition(position_id="END-TO-END", **values)


def _normal_behavioural_data() -> BehaviouralData:
    return BehaviouralData(
        average_utilization=0.50,
        overdraft_days=2.0,
        payment_delay_days=5.0,
        exposure_growth=0.05,
    )


def _normal_debt_data() -> DebtSustainabilityData:
    return DebtSustainabilityData(
        cash_flow_available_for_debt_service=150.0,
        debt_service=100.0,
        ebitda=100.0,
        interest_expense=50.0,
    )


def _attention_debt_data() -> DebtSustainabilityData:
    return DebtSustainabilityData(
        cash_flow_available_for_debt_service=80.0,
        debt_service=100.0,
        ebitda=200.0,
        interest_expense=50.0,
    )


def test_all_three_core_sections_normal_flow_to_normal_final_assessment() -> None:
    case = _case_service().assess(
        _position(),
        behavioural_data=_normal_behavioural_data(),
        debt_sustainability_data=_normal_debt_data(),
    )

    assert case.financial_analysis.status == SectionStatus.NORMAL
    assert case.behavioural_analysis.status == SectionStatus.NORMAL
    assert case.debt_sustainability.status == SectionStatus.NORMAL
    assert case.final_assessment is not None
    assert case.final_assessment.status == SectionStatus.NORMAL


def test_one_behavioural_attention_section_flows_to_attention_final_assessment() -> None:
    case = _case_service().assess(
        _position(),
        behavioural_data=BehaviouralData(
            average_utilization=0.95,
            overdraft_days=2.0,
            payment_delay_days=5.0,
            exposure_growth=0.05,
        ),
        debt_sustainability_data=_normal_debt_data(),
    )

    assert case.financial_analysis.status == SectionStatus.NORMAL
    assert case.behavioural_analysis.status == SectionStatus.ATTENTION
    assert case.debt_sustainability.status == SectionStatus.NORMAL
    assert case.final_assessment is not None
    assert case.final_assessment.status == SectionStatus.ATTENTION
    assert [
        result.rule_id
        for result in case.behavioural_analysis.evidence
        if result.status == RuleStatus.TRIGGERED
    ] == ["B001"]


def test_attention_in_two_different_core_sections_escalates_to_critical() -> None:
    case = _case_service().assess(
        _position(),
        behavioural_data=BehaviouralData(
            average_utilization=0.95,
            overdraft_days=2.0,
            payment_delay_days=5.0,
            exposure_growth=0.05,
        ),
        debt_sustainability_data=_attention_debt_data(),
    )

    assert case.financial_analysis.status == SectionStatus.NORMAL
    assert case.behavioural_analysis.status == SectionStatus.ATTENTION
    assert case.debt_sustainability.status == SectionStatus.ATTENTION
    assert case.final_assessment is not None
    assert case.final_assessment.status == SectionStatus.CRITICAL

    assert [
        result.rule_id
        for result in case.behavioural_analysis.evidence
        if result.status == RuleStatus.TRIGGERED
    ] == ["B001"]
    assert [
        result.rule_id
        for result in case.debt_sustainability.evidence
        if result.status == RuleStatus.TRIGGERED
    ] == ["DS001", "DS003"]


def test_financial_and_debt_attention_also_escalate_to_critical() -> None:
    case = _case_service().assess(
        _position(revenue_growth=-0.15),
        behavioural_data=_normal_behavioural_data(),
        debt_sustainability_data=_attention_debt_data(),
    )

    assert case.financial_analysis.status == SectionStatus.ATTENTION
    assert case.behavioural_analysis.status == SectionStatus.NORMAL
    assert case.debt_sustainability.status == SectionStatus.ATTENTION
    assert case.final_assessment is not None
    assert case.final_assessment.status == SectionStatus.CRITICAL
