"""Financial analysis presentation for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import (
    rule_direction,
    rule_indicator,
    rule_status,
    threshold_distance,
    threshold_relation,
)


def build_indicator_analysis_frame(section: Any) -> pd.DataFrame:
    """Build analyst-facing indicator evidence without recalculating rule outcomes."""
    rows = []
    for rule in section.evidence:
        value = getattr(rule, "value", None)
        threshold = getattr(rule, "threshold", None)
        if value is None or threshold is None:
            continue

        value = float(value)
        threshold = float(threshold)
        distance = threshold_distance(value, threshold, rule_direction(rule))
        relation = threshold_relation(distance)

        rows.append(
            {
                "Rule": getattr(rule, "rule_id", ""),
                "Indicator": rule_indicator(rule),
                "Value": value,
                "Threshold": threshold,
                "Status": rule_status(rule),
                "Distance": distance,
                "Relation": relation,
            }
        )
    return pd.DataFrame(rows)


def _indicator_frame(section: Any) -> pd.DataFrame:
    """Build the compact indicator table used by threshold visualizations."""
    frame = build_indicator_analysis_frame(section)
    if frame.empty:
        return frame
    return frame[["Indicator", "Value", "Threshold", "Status", "Rule"]]


def _threshold_distance_frame(section: Any) -> pd.DataFrame:
    """Build a direction-aware distance from threshold for non-zero thresholds."""
    frame = build_indicator_analysis_frame(section)
    if frame.empty:
        return frame
    frame = frame.dropna(subset=["Distance"])
    if frame.empty:
        return pd.DataFrame()
    return frame.set_index("Indicator")[["Distance"]].rename(
        columns={"Distance": "Threshold distance"}
    )


def _render_threshold_distance_chart(section: Any, title: str) -> None:
    frame = _threshold_distance_frame(section)
    if frame.empty:
        return
    st.markdown(f"**{title}**")
    st.caption(
        "0.0 = configured threshold; positive values are on the worse side of the threshold, "
        "negative values on the better side. Zero-threshold indicators remain in the evidence table."
    )
    st.bar_chart(frame, horizontal=True)


def _render_risk_signal_ranking(section: Any) -> None:
    """Rank triggered indicators by normalized distance from their thresholds."""
    frame = build_indicator_analysis_frame(section)
    if frame.empty:
        return

    signals = frame[(frame["Status"] == "TRIGGERED") & frame["Distance"].notna()]
    if signals.empty:
        return

    signals = signals.sort_values("Distance", ascending=True).set_index("Indicator")
    st.markdown("**Triggered risk signals**")
    st.caption(
        "Signals are ranked by normalized distance from the configured threshold. "
        "Positive distance indicates the worse side of the threshold."
    )
    st.bar_chart(
        signals[["Distance"]].rename(columns={"Distance": "Threshold distance"}),
        horizontal=True,
    )


def _render_financial_dimensions(section: Any) -> None:
    """Expose dimension -> indicator -> evidence -> finding for analysts."""
    dimensions = getattr(section, "dimensions", {}) or {}
    if not dimensions:
        return

    findings_by_rule = {}
    for finding in getattr(section, "findings", []):
        result = getattr(finding, "result", None)
        rule_id = getattr(result, "rule_id", "")
        if rule_id:
            findings_by_rule[rule_id] = finding

    st.markdown("**Analytical Dimensions**")
    st.caption(
        "Financial indicators are grouped into analytical dimensions. This view is descriptive only "
        "and does not introduce a new risk score or alter the assessment decision."
    )

    rows = []
    for dimension, rules in dimensions.items():
        rule_list = list(rules or [])
        statuses = [rule_status(rule) for rule in rule_list]
        triggered = sum(status == "TRIGGERED" for status in statuses)
        evaluable = sum(status != "NOT_EVALUABLE" for status in statuses)
        if "TRIGGERED" in statuses:
            dimension_status = "TRIGGERED"
        elif evaluable:
            dimension_status = "NOT_TRIGGERED"
        else:
            dimension_status = "NOT_EVALUABLE"

        rows.append(
            {
                "Analytical dimension": dimension,
                "Indicators": len(rule_list),
                "Triggered": triggered,
                "Evaluable": evaluable,
                "Status": dimension_status,
            }
        )

    dimension_frame = pd.DataFrame(rows)
    if dimension_frame.empty:
        return

    chart_frame = dimension_frame.set_index("Analytical dimension")[["Triggered"]]
    st.bar_chart(chart_frame, horizontal=True)
    st.dataframe(dimension_frame, use_container_width=True, hide_index=True)

    for dimension, rules in dimensions.items():
        rule_list = list(rules or [])
        if not rule_list:
            continue

        st.markdown(f"**{dimension}**")
        detail_rows = []
        for rule in rule_list:
            detail_rows.append(
                {
                    "Rule": getattr(rule, "rule_id", ""),
                    "Indicator": rule_indicator(rule),
                    "Value": getattr(rule, "value", None),
                    "Threshold": getattr(rule, "threshold", None),
                    "Status": rule_status(rule),
                }
            )
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

        for rule in rule_list:
            rule_id = getattr(rule, "rule_id", "")
            if rule_status(rule) != "TRIGGERED":
                continue
            finding = findings_by_rule.get(rule_id)
            if finding is None:
                continue
            result = getattr(finding, "result", None)
            reason = getattr(result, "reason", None) or getattr(finding, "comment", "")
            if reason:
                indicator = rule_indicator(rule)
                st.info(f"**Finding · {indicator} ({rule_id})**\n\n{reason}")


def render_financial_analysis(section: Any) -> None:
    """Render financial indicators and their deterministic threshold evidence."""
    _render_financial_dimensions(section)
    _render_risk_signal_ranking(section)
    _render_threshold_distance_chart(section, "Indicator position vs threshold")

    frame = build_indicator_analysis_frame(section)
    if not frame.empty:
        st.markdown("**Indicator evidence**")
        display_frame = frame.copy()
        display_frame["Distance"] = display_frame["Distance"].map(
            lambda value: "—" if pd.isna(value) else f"{value:+.0%}"
        )
        st.dataframe(display_frame, use_container_width=True, hide_index=True)


def render_behavioural_analysis(section: Any) -> None:
    """Render behavioural indicators against their configured thresholds."""
    _render_threshold_distance_chart(section, "Behavioural indicators vs threshold")


def render_debt_analysis(section: Any) -> None:
    """Render debt-service indicators and the deterministic cash-flow buffer."""
    _render_threshold_distance_chart(section, "Debt-service indicators vs threshold")

    buffer_rule = next(
        (rule for rule in section.evidence if getattr(rule, "rule_id", "") == "DS003"),
        None,
    )
    if buffer_rule is not None and getattr(buffer_rule, "value", None) is not None:
        value = float(buffer_rule.value)
        st.metric("Cash Flow Debt-Service Buffer", f"{value:,.2f}")
