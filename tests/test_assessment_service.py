from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition

from src.rules.profitability_rules import NegativeEbitdaRule
from src.rules.revenue_rules import RevenueGrowthRule
from src.rules.margin_rules import EbitdaMarginRule
from src.rules.leverage_rules import PfnToEbitdaRule

from src.services.assessment_service import AssessmentService
from config.rules import DEFAULT_RULES

def test_assessment_service_generates_comments():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0
    )

    rule_engine = RuleEngine(DEFAULT_RULES)
    comment_engine = CommentEngine()

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
    )

    comments = service.assess(position)

    assert len(comments) == 4

    assert comments[0].rule_id == "R001"
    assert comments[0].text == "Revenue deterioration detected."

    assert comments[1].rule_id == "R002"
    assert comments[1].text == "Negative EBITDA detected."

    assert comments[2].rule_id == "R003"
    assert comments[2].text == "EBITDA margin is below acceptable threshold."

    assert comments[3].rule_id == "R004"
    assert comments[3].text == "Leverage is above acceptable threshold."
