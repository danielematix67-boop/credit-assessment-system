import pytest

from src.comments.comment import Comment
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@pytest.fixture
def rule_result():
    return RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test Rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.fixture
def comment():
    return Comment(
        rule_id="TEST_RULE",
        text="Test comment.",
    )


@pytest.fixture
def finding(rule_result, comment):
    return RuleFinding(
        result=rule_result,
        comment=comment,
    )


def test_rule_finding_stores_result_and_comment(
    finding,
    rule_result,
    comment,
):
    assert finding.result is rule_result
    assert finding.comment is comment


def test_rule_finding_links_result_and_comment_by_rule_id(
    finding,
):
    assert finding.result.rule_id == finding.comment.rule_id


def test_rule_finding_is_immutable(finding):
    with pytest.raises(AttributeError):
        finding.comment = Comment(
            rule_id=finding.comment.rule_id,
            text="Modified comment.",
        )