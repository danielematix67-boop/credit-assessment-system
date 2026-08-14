import pytest

from src.comments.comment import Comment


@pytest.mark.parametrize(
    "rule_id, text",
    [
        ("R001", "Comment for rule R001."),
        ("R002", "Comment for rule R002."),
        ("CUSTOM_RULE", "Generic rule comment."),
    ],
)
def test_comment_stores_rule_id_and_text(rule_id, text):
    comment = Comment(
        rule_id=rule_id,
        text=text,
    )

    assert comment.rule_id == rule_id
    assert comment.text == text


def test_comment_is_immutable():
    comment = Comment(
        rule_id="R001",
        text="Original comment.",
    )

    with pytest.raises(AttributeError):
        comment.text = "Modified comment."