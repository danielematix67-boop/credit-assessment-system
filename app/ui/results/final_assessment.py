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
    limitations = list(getattr(final_assessment, "limitations", []) or [])

    st.markdown("### Final Assessment")

    rows = [
        {
            "Analysis area": getattr(section, "name", "Unknown"),
            "Status": _status_value(getattr(section, "status", None)),
            "Evidence": len(getattr(section, "evidence", []) or []),
            "Findings": len(getattr(section, "findings", []) or []),
        }
        for section in sections
    ]

    frame = pd.DataFrame(rows)
    if not frame.empty:
        st.dataframe(frame, use_container_width=True, hide_index=True)

    if limitations:
        with st.expander("Assessment limitations", expanded=False):
            for limitation in limitations:
                st.write(f"• {limitation}")

    st.caption(
        "Deterministic consolidation of macro-area statuses; no weighted score or LLM decision is introduced."
    )
