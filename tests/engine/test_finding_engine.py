from unittest.mock import MagicMock

import pytest

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.engine.finding_engine import FindingEngine
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def triggered_result():
    return RuleResult(
        rule_id="RULE_ID",
        rule_name="Rule name",
        category="category",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.fixture
def comment(triggered_result):
    return Comment(
        rule_id=triggered_result.rule_id,
        text="Generated comment",
    )


@pytest.fixture
def comment_engine():
    return MagicMock(spec=CommentEngine)


@pytest.fixture
def finding_engine(comment_engine):
    return FindingEngine(comment_engine)


# ============================================================
# Comment generation
# ============================================================


def test_finding_engine_creates_finding_when_comment_is_available(
    triggered_result,
    comment,
    comment_engine,
    finding_engine,
):
    comment_engine.generate.return_value = comment

    finding = finding_engine.generate(triggered_result)

    assert isinstance(finding, RuleFinding)

    assert finding.result is triggered_result
    assert finding.comment is comment

    comment_engine.generate.assert_called_once_with(
        triggered_result,
    )


# ============================================================
# Missing comment
# ============================================================


def test_finding_engine_returns_none_when_comment_is_unavailable(
    triggered_result,
    comment_engine,
    finding_engine,
):
    comment_engine.generate.return_value = None

    finding = finding_engine.generate(triggered_result)

    assert finding is None

    comment_engine.generate.assert_called_once_with(
        triggered_result,
    )


# ============================================================
# Comment identity
# ============================================================


def test_finding_engine_preserves_comment_identity(
    triggered_result,
    comment,
    comment_engine,
    finding_engine,
):
    comment_engine.generate.return_value = comment

    finding = finding_engine.generate(triggered_result)

    assert finding is not None
    assert finding.comment is comment
    assert finding.comment.rule_id == triggered_result.rule_id


# ============================================================
# Comment content
# ============================================================


@pytest.mark.parametrize(
    "comment_text",
    [
        "Generated comment",
        "Business finding description",
        "Detailed assessment finding",
        "",
    ],
)
def test_finding_engine_preserves_comment_content(
    triggered_result,
    comment_engine,
    finding_engine,
    comment_text,
):
    comment = Comment(
        rule_id=triggered_result.rule_id,
        text=comment_text,
    )

    comment_engine.generate.return_value = comment

    finding = finding_engine.generate(triggered_result)

    assert finding is not None
    assert finding.comment is comment
    assert finding.comment.text == comment_text


# ============================================================
# Result preservation
# ============================================================


def test_finding_engine_preserves_original_rule_result(
    triggered_result,
    comment,
    comment_engine,
    finding_engine,
):
    comment_engine.generate.return_value = comment

    finding = finding_engine.generate(triggered_result)

    assert finding is not None
    assert finding.result is triggered_result


# ============================================================
# Delegation contract
# ============================================================


def test_finding_engine_delegates_comment_generation_to_comment_engine(
    triggered_result,
    comment,
    comment_engine,
    finding_engine,
):
    comment_engine.generate.return_value = comment

    finding_engine.generate(triggered_result)

    comment_engine.generate.assert_called_once_with(
        triggered_result,
    )
