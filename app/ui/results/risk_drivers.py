"""Cross-area risk driver presentation for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st


def _rule_status(rule: Any) -> str:
    return str(
        getattr(getattr(rule, "status", None), "value", getattr(rule, "status", ""))
    ).upper()


def _rule_direction(rule: Any) -> str:
    return str(
        getattr(
            getattr(rule, "direction", None),
            "value",
            getattr(rule, "direction", ""),
        )
    ).upper()


def _threshold_distance(
    value: float, threshold: float, direction: str
) -> float | None:
    """Return normalized distance from threshold; positive means worse."""
    if threshold == 0:
        return None
    scale = abs(threshold)
    if direction == "LOWER_IS_WORSE":
        return (threshold - value) / scale
    return (value - threshold) / scale


def build_risk_driver_frame(credit_case: Any) -> pd.DataFrame:
    """Build a cross-area ranking from deterministic triggered RuleResult data."""
    rows = []
    for section in getattr(credit_case, "sections", []) or []:
        for rule in getattr(section, "evidence", []) or []:
            if _rule_status(rule) != "TRIGGERED":
                continue

            value = getattr(rule, "value", None)
            threshold = getattr(rule, "threshold", None)
            distance = None
            relation = "Not evaluable"
            if value is not None and threshold is not None:
                value = float(value)
                threshold = float(threshold)
                distance = _threshold_distance(
                    value, threshold, _rule_direction(rule)
                )
                relation = (
                    "Threshold = 0"
                    if distance is None
                    else "Worse than threshold"
                    if distance > 0
                    else "At threshold"
                )

            rows.append(
                {
                    "Macro-area": getattr(section, "name", "Unknown"),
                    "Rule": getattr(rule, "rule_id", ""),
                    "Indicator": getattr(
                        rule, "indicator", getattr(rule, "rule_name", "Indicator")
                    ),
                    "Value": value,
                    "Threshold": threshold,
                    "Severity": str(
                        getattr(
                            getattr(rule, "severity", None),
                            "value",
                            getattr(rule, "severity", ""),
                        )
                    ).upper(),
                    "Distance": distance,
                    "Relation": relation,
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    return frame.sort_values(
        "Distance", ascending=False, na_position="last", kind="stable"
    ).reset_index(drop=True)


def render_risk_driver_overview(credit_case: Any) -> None:
    """Render the highest-priority deterministic risk drivers across macro-areas."""
    frame = build_risk_driver_frame(credit_case)
    if frame.empty:
        return

    st.markdown("### Risk Driver Overview")
    st.caption(
        "Triggered indicators are ranked across macro-areas by their normalized distance "
        "from the configured threshold. This view is descriptive and does not create a new score."
    )

    chart_frame = frame.dropna(subset=["Distance"]).head(10)
    if not chart_frame.empty:
        chart_frame = chart_frame.set_index("Indicator")[["Distance"]].rename(
            columns={"Distance": "Threshold distance"}
        )
        st.bar_chart(chart_frame, horizontal=True)

    display_frame = frame.copy()
    display_frame["Distance"] = display_frame["Distance"].map(
        lambda value: "—" if pd.isna(value) else f"{value:+.0%}"
    )
    st.dataframe(display_frame, use_container_width=True, hide_index=True)
