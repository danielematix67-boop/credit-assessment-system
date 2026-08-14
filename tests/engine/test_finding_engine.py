from unittest.mock import MagicMock

import pytest

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.engine.finding_engine import FindingEngine
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@pytest.fixture
def triggered_result():
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
def comment_engine():
    return MagicMock(spec=CommentEngine)


def test_finding_engine_generates_rule_finding_from_comment(
    triggered_result,
    comment,
    comment_engine,
):
    comment_engine.generate.return_value = comment

    engine = FindingEngine(comment_engine)

    finding = engine.generate(triggered_result)

    assert isinstance(finding, RuleFinding)
    assert finding.result is triggered_result
    assert finding.comment is comment

    comment_engine.generate.assert_called_once_with(
        triggered_result
    )


def test_finding_engine_returns_none_when_comment_is_not_available(
    triggered_result,
    comment_engine,
):
    comment_engine.generate.return_value = None

    engine = FindingEngine(comment_engine)

    finding = engine.generate(triggered_result)

    assert finding is None

    comment_engine.generate.assert_called_once_with(
        triggered_result
    )


@pytest.mark.parametrize(
    "comment_text",
    [
        "Test comment.",
        "Custom business comment.",
        "A more detailed finding description.",
        "",
    ],
)
def test_finding_engine_preserves_comment_content(
    triggered_result,
    comment_engine,
    comment_text,
):
    comment = Comment(
        rule_id=triggered_result.rule_id,
        text=comment_text,
    )

    comment_engine.generate.return_value = comment

    engine = FindingEngine(comment_engine)

    finding = engine.generate(triggered_result)

    assert finding is not None
    assert finding.result is triggered_result
    assert finding.comment is comment
    assert finding.comment.rule_id == triggered_result.rule_id
    assert finding.comment.text == comment_text

    comment_engine.generate.assert_called_once_with(
        triggered_result
    )