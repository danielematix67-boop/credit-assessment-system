from typing import Any

import streamlit as st

from app.ui.components import render_section_header


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status or "NOT_EVALUABLE")).upper()


def _finding_text(finding: Any) -> str:
    return str(getattr(finding, "text", finding or ""))


def render_executive_synthesis(result: Any) -> None:
    """Render the executive synthesis from deterministic case evidence and report narrative."""
    credit_case = getattr(result, "credit_case", None)
    report = getattr(result, "report", None)
    if credit_case is None or report is None:
        return

    final_assessment = getattr(credit_case, "final_assessment", None)
    if final_assessment is None:
        return

    render_section_header(
        "06 · Executive Synthesis",
        "Management-level synthesis of the deterministic assessment and its supporting evidence.",
    )

    final_status = _status_value(getattr(final_assessment, "status", None))
    risk_sections = list(getattr(final_assessment, "risk_sections", []) or [])
    normal_sections = list(getattr(final_assessment, "normal_sections", []) or [])
    limitations = list(getattr(final_assessment, "limitations", []) or [])

    with st.container(border=True):
        st.caption("Deterministic assessment conclusion")
        st.markdown(f"### {final_status}")
        st.caption(
            "The status above is calculated by the deterministic assessment layer. "
            "The reporting layer does not modify the decision."
        )

    columns = st.columns(2)
    with columns[0]:
        st.markdown("**Key risk areas**")
        if risk_sections:
            for section in risk_sections:
                st.write(f"• {section}")
        else:
            st.write("No risk or attention area identified.")

    with columns[1]:
        st.markdown("**Normal areas / mitigants**")
        if normal_sections:
            for section in normal_sections:
                st.write(f"• {section}")
        else:
            st.write("No fully normal area identified.")

    analysis = getattr(result, "analysis", None)
    risk_factors = list(getattr(analysis, "risk_factors", []) or []) if analysis else []
    if risk_factors:
        with st.expander("Material risk findings", expanded=True):
            for finding in risk_factors:
                text = _finding_text(finding)
                if text:
                    st.write(f"• {text}")

    if limitations:
        with st.expander("Assessment limitations", expanded=False):
            for limitation in limitations:
                st.write(f"• {limitation}")

    render_section_header(
        "Executive Narrative",
        "Narrative generated from deterministic findings; it does not create or alter the credit decision.",
    )
    with st.container(border=True):
        narrative = str(getattr(report, "executive_summary", "No executive summary available."))
        lines = narrative.split("\n\n", 1)
        if len(lines) == 2 and lines[0].lower().startswith("assessment status:"):
            narrative = lines[1]
        st.markdown(narrative)
