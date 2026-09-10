from typing import Any

import pandas as pd
import streamlit as st


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status or "NOT_EVALUABLE")).upper()


def render_final_assessment(credit_case: Any) -> None:
    """Render the deterministic final assessment as a compact analyst conclusion."""
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
        "Deterministic consolidation of macro-area outcomes; no weighted score or LLM decision is introduced."
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
        rows.append(
            {
                "Analysis area": getattr(section, "name", "Unknown"),
                "Status": _status_value(getattr(section, "status", None)),
                "Evidence": len(getattr(section, "evidence", []) or []),
                "Findings": len(getattr(section, "findings", []) or []),
            }
        )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        st.dataframe(frame, use_container_width=True, hide_index=True)

    if limitations:
        with st.expander("Assessment limitations", expanded=False):
            for limitation in limitations:
                st.write(f"• {limitation}")

    st.caption(
        "Decision provenance: Final Assessment Service → deterministic aggregation of macro-area statuses."
    )
