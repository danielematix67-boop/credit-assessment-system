from src.comments.comment import Comment
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.models.rule_finding import RuleFinding
from src.rules.result import RuleResult


def test_rule_finding_stores_result_and_comment():
    rule_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    comment = Comment(
        rule_id="R001",
        text=(
            "Revenue deterioration detected. "
            "Revenue growth: -15.0% (threshold: -10.0%)."
        ),
    )

    finding = RuleFinding(
        result=rule_result,
        comment=comment,
    )

    assert finding.result == rule_result
    assert finding.comment == comment


def test_rule_finding_links_result_and_comment_by_rule_id():
    rule_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    comment = Comment(
        rule_id="R001",
        text="Revenue deterioration detected.",
    )

    finding = RuleFinding(
        result=rule_result,
        comment=comment,
    )

    assert finding.result.rule_id == finding.comment.rule_id


def test_rule_finding_is_immutable():
    rule_result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    comment = Comment(
        rule_id="R001",
        text="Revenue deterioration detected.",
    )

    finding = RuleFinding(
        result=rule_result,
        comment=comment,
    )

    try:
        finding.comment = comment
        assert False, "RuleFinding should be immutable"
    except AttributeError:
        pass