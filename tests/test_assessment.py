from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.profitability_rules import NegativeEbitdaRule
from src.rules.revenue_rules import RevenueGrowthRule
from src.services.assessment_service import AssessmentService


def test_assessment_service_generates_assessment():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rules = [
        RevenueGrowthRule(),
        NegativeEbitdaRule(),
    ]

    rule_engine = RuleEngine(rules)
    comment_engine = CommentEngine()

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
    )

    assessment = service.assess(position)

    assert assessment.position_id == "POS001"

    assert len(assessment.rule_results) == 2

    assert assessment.rule_results[0].rule_id == "R001"
    assert assessment.rule_results[1].rule_id == "R002"

    assert len(assessment.comments) == 2

    assert assessment.comments[0].rule_id == "R001"
    assert assessment.comments[0].text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0%."
    )

    assert assessment.comments[1].rule_id == "R002"
    assert assessment.comments[1].text == (
        "Negative EBITDA detected. "
        "EBITDA: €-50,000."
    )

