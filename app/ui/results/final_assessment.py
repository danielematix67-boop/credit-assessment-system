from typing import Any

import pandas as pd
import streamlit as st


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status or "NOT_EVALUABLE")).upper()


def render_final_assessment(credit_case: Any) -> None:
    """Render the deterministic final assessment as a compact area summary."""
    final_assessment = getattr(credit_case, "final_assessment", None)
    if final_assessment is None:
        return

    sections = list(getattr(credit_case, "sections", []) or [])
    limitations = list(getattr(final_assessment, "limitations", []) or [])

    st.markdown("### Final Assessment")
    st.caption("Macro-area statuses consolidated by the deterministic assessment engine.")

    rows = [
        {
            "Assessment area": getattr(section, "name", "Unknown"),
            "Status": _status_value(getattr(section, "status", None)),
            "Evidence": len(getattr(section, "evidence", []) or []),
            "Findings": len(getattr(section, "findings", []) or []),
        }
        for section in sections
    ]

    frame = pd.DataFrame(rows)
    if not frame.empty:
        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Assessment area": st.column_config.TextColumn("Assessment area", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Evidence": st.column_config.NumberColumn("Evidence", width="small"),
                "Findings": st.column_config.NumberColumn("Findings", width="small"),
            },
        )

    if limitations:
        with st.expander(f"Assessment limitations ({len(limitations)})", expanded=False):
            for limitation in limitations:
                st.write(f"• {limitation}")

    st.caption("No weighted score or LLM decision is introduced.")
