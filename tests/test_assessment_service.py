from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.models.assessment_status import AssessmentStatus
from src.rules.base.status import RuleStatus
from src.rules.registry import get_default_rules
from src.services.assessment_service import AssessmentService
from src.services.assessment_status_calculator import AssessmentStatusCalculator


def test_assessment_service_generates_assessment():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    rule_engine = RuleEngine(get_default_rules())
    comment_engine = CommentEngine()
    status_calculator = AssessmentStatusCalculator()

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )

    assessment = service.assess(position)

    assert assessment.position_id == "POS001"
    assert assessment.status == AssessmentStatus.CRITICAL

    assert len(assessment.rule_results) == 5
    assert len(assessment.comments) == 4

    # R001
    assert assessment.comments[0].rule_id == "R001"
    assert assessment.comments[0].text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0% (threshold: -10.0%)."
    )

    # R003
    assert assessment.comments[1].rule_id == "R003"
    assert assessment.comments[1].text == (
        "EBITDA margin is below the acceptable threshold. "
        "EBITDA margin: -5.0% (threshold: 0.0%)."
    )

    # R004
    assert assessment.comments[2].rule_id == "R004"
    assert assessment.comments[2].text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x (threshold: 5.0x)."
    )

    # R005
    assert assessment.comments[3].rule_id == "R005"
    assert assessment.comments[3].text == (
        "Interest expense to EBITDA is above the acceptable threshold. "
        "Ratio: 80.0% (threshold: 60.0%)."
    )


def test_assessment_service_does_not_generate_comment_for_not_evaluable_rule():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule_engine = RuleEngine(get_default_rules())
    comment_engine = CommentEngine()
    status_calculator = AssessmentStatusCalculator()

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )

    assessment = service.assess(position)

    assert assessment.position_id == "POS002"

    assert len(assessment.rule_results) == 5
    assert len(assessment.comments) == 0

    assert assessment.rule_results[0].rule_id == "R001"
    assert assessment.rule_results[0].status == RuleStatus.NOT_EVALUABLE
    assert assessment.rule_results[0].value is None

    assert all(
        result.status != RuleStatus.NOT_EVALUABLE
        for result in assessment.rule_results[1:]
    )


def test_assessment_service_generates_no_comments_for_healthy_position():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule_engine = RuleEngine(get_default_rules())
    comment_engine = CommentEngine()
    status_calculator = AssessmentStatusCalculator()

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )

    assessment = service.assess(position)

    assert assessment.position_id == "POS003"
    assert assessment.status == AssessmentStatus.NORMAL

    assert len(assessment.rule_results) == 5
    assert len(assessment.comments) == 0

    assert all(
        result.status == RuleStatus.NOT_TRIGGERED
        for result in assessment.rule_results
    )
