from typing import Any

import streamlit as st


# ============================================================
# Responsive Position Table
# ============================================================


def render_responsive_position_table(
    rows: list[dict[str, Any]],
) -> None:
    """
    Render position data using a standard Streamlit dataframe.

    The same table representation is used on desktop, tablet
    and mobile. Horizontal scrolling is handled by Streamlit
    when the available viewport is too narrow.

    The input data structure remains unchanged.
    """

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        column_config={
            "Financial Indicator": st.column_config.TextColumn(
                "Financial Indicator",
                width="medium",
            ),
            "Value": st.column_config.TextColumn(
                "Value",
                width="medium",
            ),
            "Unit": st.column_config.TextColumn(
                "Unit",
                width="small",
            ),
            "Description": st.column_config.TextColumn(
                "What it represents",
                width="large",
            ),
        },
    )