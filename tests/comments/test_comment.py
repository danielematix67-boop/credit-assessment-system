import pytest

from src.comments.comment import Comment


def test_comment_stores_rule_id_and_text():
    comment = Comment(
        rule_id="R001",
        text=(
            "Revenue deterioration detected. "
            "Revenue growth: -15.0% (threshold: -10.0%)."
        ),
    )

    assert comment.rule_id == "R001"
    assert comment.text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0% (threshold: -10.0%)."
    )


def test_comment_is_immutable():
    comment = Comment(
        rule_id="R001",
        text="Revenue deterioration detected.",
    )

    with pytest.raises(AttributeError):
        comment.text = "Modified comment."

