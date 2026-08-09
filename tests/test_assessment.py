from src.comments.comment import Comment
from src.models.assessment import Assessment
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_assessment_stores_position_id_rule_results_and_comments():
    rule_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
    )

    comment = Comment(
        rule_id="R001",
        text=(
            "Revenue deterioration detected. "
            "Revenue growth: -15.0% (threshold: -10.0%)."
        ),
    )

    assessment = Assessment(
        position_id="POS001",
        rule_results=[rule_result],
        comments=[comment],
    )

    assert assessment.position_id == "POS001"
    assert assessment.rule_results == [rule_result]
    assert assessment.comments == [comment]
