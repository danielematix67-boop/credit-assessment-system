from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition

from src.services.assessment_service import AssessmentService
from config.rules import DEFAULT_RULES


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

    rule_engine = RuleEngine(DEFAULT_RULES)
    comment_engine = CommentEngine()

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
    )

    assessment = service.assess(position)

    assert assessment.position_id == "POS001"

    assert len(assessment.rule_results) == 5
    assert len(assessment.comments) == 4

    # R001
    assert assessment.comments[0].rule_id == "R001"
    assert assessment.comments[0].text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0%."
    )

    # R003
    assert assessment.comments[1].rule_id == "R003"
    assert assessment.comments[1].text == (
        "EBITDA margin is below acceptable threshold. "
        "EBITDA margin: -5.0%."
    )

    # R004
    assert assessment.comments[2].rule_id == "R004"
    assert assessment.comments[2].text == (
        "Leverage is above acceptable threshold. "
        "PFN to EBITDA: 6.0x."
    )

    # R005
    assert assessment.comments[3].rule_id == "R005"
    assert assessment.comments[3].text == (
        "Interest expense to EBITDA is above acceptable threshold. "
        "Ratio: 80.0%."
    )
