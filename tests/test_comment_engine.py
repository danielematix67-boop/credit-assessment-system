from src.comments.comment_engine import CommentEngine
from src.models.position import CreditPosition
from src.rules.revenue_rules import RevenueGrowthRule


def test_comment_generated_when_rule_is_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=250000,
        profit_loss=50000,
    )

    rule = RevenueGrowthRule()
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is not None
    assert comment.rule_id == "R001"
    assert comment.text == "Revenue deterioration detected."


def test_no_comment_generated_when_rule_is_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
    )

    rule = RevenueGrowthRule()
    result = rule.evaluate(position)

    engine = CommentEngine()
    comment = engine.generate(result)

    assert comment is None