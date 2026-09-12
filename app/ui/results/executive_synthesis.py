from typing import Any

import streamlit as st

from app.ui.components import render_section_header


def render_executive_synthesis(result: Any) -> None:
    """Render the executive narrative without duplicating deterministic evidence."""
    credit_case = getattr(result, "credit_case", None)
    report = getattr(result, "report", None)
    if credit_case is None or report is None:
        return

    if getattr(credit_case, "final_assessment", None) is None:
        return

    render_section_header(
        "06 · Executive Narrative",
        "Management-level narrative generated from the deterministic assessment evidence.",
    )

    with st.container(border=True):
        narrative = str(
            getattr(
                report,
                "executive_summary",
                "No executive summary available.",
            )
        )
        lines = narrative.split("\n\n", 1)
        if len(lines) == 2 and lines[0].lower().startswith("assessment status:"):
            narrative = lines[1]
        st.markdown(narrative)
