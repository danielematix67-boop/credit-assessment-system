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
def comment(rule_result):
    return Comment(
        rule_id=rule_result.rule_id,
        text="Test comment.",
    )


@pytest.fixture
def finding(rule_result, comment):
    return RuleFinding(
        result=rule_result,
        comment=comment,
    )


def test_rule_finding_preserves_provided_objects(
    finding,
    rule_result,
    comment,
):
    assert finding.result is rule_result
    assert finding.comment is comment


def test_rule_finding_preserves_rule_id_relationship(
    finding,
):
    assert finding.result.rule_id == finding.comment.rule_id


def test_rule_finding_preserves_result_rule_id(
    finding,
    rule_result,
):
    assert finding.result.rule_id == rule_result.rule_id


def test_rule_finding_preserves_comment_rule_id(
    finding,
    comment,
):
    assert finding.comment.rule_id == comment.rule_id


def test_rule_finding_is_immutable(finding):
    with pytest.raises(AttributeError):
        finding.comment = None

    with pytest.raises(AttributeError):
        finding.result = None