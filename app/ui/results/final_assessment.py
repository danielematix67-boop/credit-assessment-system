from typing import Any

import pandas as pd
import streamlit as st


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status or "NOT_EVALUABLE")).upper()


def render_final_assessment(credit_case: Any) -> None:
    """Render the deterministic final assessment as an analyst conclusion."""
    final_assessment = getattr(credit_case, "final_assessment", None)
    if final_assessment is None:
        return

    sections = list(getattr(credit_case, "sections", []) or [])
    final_status = _status_value(getattr(final_assessment, "status", None))
    risk_sections = list(getattr(final_assessment, "risk_sections", []) or [])
    normal_sections = list(getattr(final_assessment, "normal_sections", []) or [])
    limitations = list(getattr(final_assessment, "limitations", []) or [])

    st.markdown("### Final Assessment")
    st.caption(
        "The final assessment consolidates the deterministic macro-area outcomes. "
        "It does not introduce a weighted score or an LLM-generated decision."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final status", final_status)
    with col2:
        st.metric("Risk / attention areas", len(risk_sections))
    with col3:
        st.metric("Normal areas", len(normal_sections))

    rows = []
    for section in sections:
        status = _status_value(getattr(section, "status", None))
        rows.append(
            {
                "Analysis area": getattr(section, "name", "Unknown"),
                "Status": status,
                "Evidence": len(getattr(section, "evidence", []) or []),
                "Findings": len(getattr(section, "findings", []) or []),
            }
        )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        st.markdown("**Macro-area conclusion**")
        st.dataframe(frame, use_container_width=True, hide_index=True)

        counts = frame["Status"].value_counts().reindex(
            ["NORMAL", "ATTENTION", "CRITICAL", "NOT_EVALUABLE"], fill_value=0
        )
        st.bar_chart(counts, horizontal=True)

    if risk_sections:
        st.markdown("**Areas requiring attention**")
        for section_name in risk_sections:
            section = next(
                (item for item in sections if getattr(item, "name", "") == section_name),
                None,
            )
            status = _status_value(getattr(section, "status", None)) if section else "UNKNOWN"
            st.warning(f"**{section_name}** — {status}")

    if normal_sections:
        with st.expander("Normal areas", expanded=False):
            for section_name in normal_sections:
                st.write(f"• {section_name}")

    if limitations:
        with st.expander("Assessment limitations", expanded=False):
            for limitation in limitations:
                st.write(f"• {limitation}")

    st.caption(
        "Decision provenance: Final Assessment Service → deterministic aggregation of macro-area statuses."
    )
