from pathlib import Path

from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.engine.rule_engine import RuleEngine
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.discovery import discover_rules
from src.services.assessment_service import AssessmentService
from src.services.credit_assessment_case_service import CreditAssessmentCaseService
from src.services.final_assessment_service import FinalAssessmentService
from src.services.position_validator import CreditPositionValidator
from src.rules.base.status import RuleStatus

RULES_CONFIG_PATH = Path("config/financial_analysis_rules.yaml")


def _case_service() -> CreditAssessmentCaseService:
    discover_rules()
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    rules = [Rule.get_registered_rule(config.rule_id)(config) for config in configs]
    assessment_service = AssessmentService(
        rule_engine=RuleEngine(rules),
        comment_engine=CommentEngine(),
        status_calculator=__import__(
            "src.services.assessment_status_calculator",
            fromlist=["AssessmentStatusCalculator"],
        ).AssessmentStatusCalculator(),
        position_validator=CreditPositionValidator(),
    )
    return CreditAssessmentCaseService(assessment_service)


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


def test_financial_rules_flow_from_position_to_normal_final_assessment() -> None:
    case = _case_service().assess(_position())

    assert case.financial_analysis.status == AssessmentStatus.NORMAL
    assert case.final_assessment is not None
    assert case.final_assessment.status == AssessmentStatus.NORMAL
    assert all(
        result.status == RuleStatus.NOT_TRIGGERED
        for result in case.financial_analysis.evidence
    )


def test_one_triggered_financial_rule_flows_to_attention_final_assessment() -> None:
    case = _case_service().assess(_position(revenue_growth=-0.15))

    assert case.financial_analysis.status == AssessmentStatus.ATTENTION
    assert case.final_assessment is not None
    assert case.final_assessment.status == AssessmentStatus.ATTENTION
    triggered = [
        result.rule_id
        for result in case.financial_analysis.evidence
        if result.status == RuleStatus.TRIGGERED
    ]
    assert triggered == ["R001"]


def test_two_triggered_financial_rules_flow_to_critical_final_assessment() -> None:
    case = _case_service().assess(
        _position(revenue_growth=-0.15, nfp_to_ebitda=6.0)
    )

    assert case.financial_analysis.status == AssessmentStatus.CRITICAL
    assert case.final_assessment is not None
    assert case.final_assessment.status == AssessmentStatus.CRITICAL
    triggered = [
        result.rule_id
        for result in case.financial_analysis.evidence
        if result.status == RuleStatus.TRIGGERED
    ]
    assert triggered == ["R001", "R004"]


def test_non_triggered_rules_do_not_escalate_final_assessment() -> None:
    case = _case_service().assess(
        _position(
            revenue_growth=-0.05,
            ebitda_margin=0.05,
            nfp_to_ebitda=4.0,
            interest_expense=40.0,
            change_in_finished_goods_inventory=10.0,
        )
    )

    assert case.final_assessment is not None
    assert case.final_assessment.status == AssessmentStatus.NORMAL
    assert all(
        result.status == RuleStatus.NOT_TRIGGERED
        for result in case.financial_analysis.evidence
    )
