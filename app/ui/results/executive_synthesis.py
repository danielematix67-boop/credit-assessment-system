from typing import Any

import streamlit as st

from app.ui.components import render_section_header


def _finding_text(finding: Any) -> str:
    return str(getattr(finding, "text", finding or ""))


def render_executive_synthesis(result: Any) -> None:
    """Render the executive narrative without duplicating the deterministic conclusion."""
    credit_case = getattr(result, "credit_case", None)
    report = getattr(result, "report", None)
    if credit_case is None or report is None:
        return

    if getattr(credit_case, "final_assessment", None) is None:
        return

    render_section_header(
        "06 · Executive Narrative",
        "Management-level narrative generated from the deterministic assessment.",
    )

    analysis = getattr(result, "analysis", None)
    risk_factors = list(getattr(analysis, "risk_factors", []) or []) if analysis else []
    if risk_factors:
        with st.expander("Material risk findings", expanded=False):
            for finding in risk_factors:
                text = _finding_text(finding)
                if text:
                    st.write(f"• {text}")

    with st.container(border=True):
        narrative = str(getattr(report, "executive_summary", "No executive summary available."))
        lines = narrative.split("\n\n", 1)
        if len(lines) == 2 and lines[0].lower().startswith("assessment status:"):
            narrative = lines[1]
        st.markdown(narrative)
