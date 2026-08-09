# Comment templates define the human-readable messages associated with each rule.
#
# Templates should remain separate from rule logic so that wording can be changed
# without modifying the rules.


COMMENTS = {
    "R001": (
        "Revenue deterioration detected. "
        "Revenue growth: {value:.1%} "
        "(threshold: {threshold:.1%})."
    ),

    "R002": (
        "Negative EBITDA detected. "
        "EBITDA: €{value:,.0f} "
        "(threshold: €{threshold:,.0f})."
    ),

    "R003": (
        "EBITDA margin is below the acceptable threshold. "
        "EBITDA margin: {value:.1%} "
        "(threshold: {threshold:.1%})."
    ),

    "R004": (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: {value:.1f}x "
        "(threshold: {threshold:.1f}x)."
    ),

    "R005": (
        "Interest expense to EBITDA is above the acceptable threshold. "
        "Ratio: {value:.1%} "
        "(threshold: {threshold:.1%})."
    ),
}
