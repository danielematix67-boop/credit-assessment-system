from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.profitability_rules import NegativeEbitdaRule
from src.rules.revenue_rules import RevenueGrowthRule
from src.services.assessment_service import AssessmentService


def test_assessment_service_generates_comments():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
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

    comments = service.assess(position)

    assert len(comments) == 2

    assert comments[0].rule_id == "R001"
    assert comments[0].text == "Revenue deterioration detected."

    assert comments[1].rule_id == "R002"
    assert comments[1].text == "Negative EBITDA detected."