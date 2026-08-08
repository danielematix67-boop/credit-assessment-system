from src.comments.comment import Comment


COMMENTS = {
    "R001": Comment(
        rule_id="R001",
        text="Revenue deterioration detected."
    ),

    "R002": Comment(
        rule_id="R002",
        text="Negative EBITDA detected."
    ),

    "R003": Comment(
        rule_id="R003",
        text="EBITDA margin is below acceptable threshold."
    ),

    "R004": Comment(
        rule_id="R004",
        text="Leverage is above acceptable threshold."
    ),

    "R005": Comment(
        rule_id="R005",
        text="Interest coverage is below acceptable threshold."
    ),
}