from pathlib import Path

from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.engine.rule_engine import RuleEngine
from src.models.assessment_status import AssessmentStatus
from src.models.behavioural_data import BehaviouralData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
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


def _workflow() -> AssessmentWorkflow:
    discover_rules()
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    rules = [Rule.get_registered_rule(config.rule_id)(config) for config in configs]
    assessment_service = AssessmentService(
        rule_engine=RuleEngine(rules),
        comment_engine=CommentEngine(),
        status_calculator=AssessmentStatusCalculator(),
        position_validator=CreditPositionValidator(),
    )
    case_service = CreditAssessmentCaseService(
        assessment_service,
        behavioural_assessment_service=BehaviouralAssessmentService(),
        debt_sustainability_assessment_service=DebtSustainabilityAssessmentService(),
        final_assessment_service=FinalAssessmentService(),
    )
    deterministic_generator = DeterministicReportGenerator()
    return AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=CaseAnalysisAgent(),
        reporting_agent=ReportingAgent(
            report_generator=deterministic_generator,
            fallback_generator=deterministic_generator,
        ),
        reporting_mode="Deterministic",
        credit_case_service=case_service,
        case_analysis_agent=CaseAnalysisAgent(),
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
    return CreditPosition(position_id="WORKFLOW-END-TO-END", **values)


def _normal_behavioural_data() -> BehaviouralData:
    return BehaviouralData(
        average_utilization=0.50,
        overdraft_days=2.0,
        payment_delay_days=5.0,
        exposure_growth=0.05,
    )


def _attention_behavioural_data() -> BehaviouralData:
    return BehaviouralData(
        average_utilization=0.95,
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


def test_end_to_end_workflow_preserves_normal_decision_to_report() -> None:
    result = _workflow().run(
        _position(),
        behavioural_data=_normal_behavioural_data(),
        debt_sustainability_data=_normal_debt_data(),
    )

    assert result.credit_case is not None
    assert result.credit_case.final_assessment is not None
    assert result.credit_case.final_assessment.status.value == "NORMAL"
    assert result.analysis.assessment_status is AssessmentStatus.NORMAL
    assert result.report.assessment_status is AssessmentStatus.NORMAL
    assert result.assessment.status is AssessmentStatus.NORMAL
    assert result.report_generator_used == "PRIMARY"
    assert result.execution_metadata is not None
    assert result.execution_metadata.fallback_used is False


def test_end_to_end_workflow_preserves_attention_decision_to_report() -> None:
    result = _workflow().run(
        _position(),
        behavioural_data=_attention_behavioural_data(),
        debt_sustainability_data=_normal_debt_data(),
    )

    assert result.credit_case is not None
    assert result.credit_case.final_assessment is not None
    assert result.credit_case.final_assessment.status.value == "ATTENTION"
    assert result.analysis.assessment_status is AssessmentStatus.ATTENTION
    assert result.report.assessment_status is AssessmentStatus.ATTENTION
    assert result.assessment.status is AssessmentStatus.ATTENTION


def test_end_to_end_workflow_preserves_cross_macro_critical_decision_to_report() -> None:
    result = _workflow().run(
        _position(),
        behavioural_data=_attention_behavioural_data(),
        debt_sustainability_data=_attention_debt_data(),
    )

    assert result.credit_case is not None
    assert result.credit_case.final_assessment is not None
    assert result.credit_case.financial_analysis.status.value == "NORMAL"
    assert result.credit_case.behavioural_analysis.status.value == "ATTENTION"
    assert result.credit_case.debt_sustainability.status.value == "ATTENTION"
    assert result.credit_case.final_assessment.status.value == "CRITICAL"

    assert result.assessment.status is AssessmentStatus.CRITICAL
    assert result.analysis.assessment_status is AssessmentStatus.CRITICAL
    assert result.report.assessment_status is AssessmentStatus.CRITICAL

    assert result.report.position_id == result.analysis.position_id
    assert result.report.position_id == result.credit_case.position.position_id
    assert result.report_generator_used == "PRIMARY"
    assert result.execution_metadata is not None
    assert result.execution_metadata.reporting_mode == "Deterministic"
    assert result.execution_metadata.fallback_used is False
