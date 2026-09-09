from typing import Any

import streamlit as st


def _rules(result: Any) -> list[Any]:
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _value(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _enum_value(value: Any, default: str = "—") -> str:
    return str(getattr(value, "value", value or default))


def render_evidence_chain(result: Any) -> None:
    """Show the deterministic chain from indicator evidence to assessment status."""
    rules = _rules(result)
    if not rules:
        return

    assessment = getattr(result, "assessment", None)
    assessment_status = _enum_value(getattr(assessment, "status", None), "Unknown")

    st.markdown("#### Evidence Chain")
    st.caption(
        "Each rule is traced from the financial indicator to the configured threshold, "
        "deterministic outcome and severity. The final assessment is shown separately "
        "as the outcome of the Rule Engine."
    )

    for rule in rules:
        rule_id = str(getattr(rule, "rule_id", "—"))
        indicator = str(
            getattr(rule, "indicator", None)
            or getattr(rule, "rule_name", "—")
        )
        value = getattr(rule, "value", None)
        threshold = getattr(rule, "threshold", None)
        status = _enum_value(getattr(rule, "status", None))
        severity = _enum_value(getattr(rule, "severity", None))
        direction = _enum_value(getattr(rule, "direction", None))
        reason = getattr(rule, "reason", None)

        with st.container(border=True):
            cols = st.columns(6)
            values = [
                ("Rule", rule_id),
                ("Indicator", indicator),
                ("Actual", _value(value)),
                ("Threshold", _value(threshold)),
                ("Direction", direction),
                ("Outcome", f"{status} · {severity}"),
            ]
            for column, (label, display_value) in zip(cols, values):
                with column:
                    st.caption(label)
                    st.write(display_value)

            if reason:
                st.caption(f"Rationale: {reason}")

    st.markdown("**Deterministic assessment outcome**")
    st.info(
        f"Assessment Status: {assessment_status}. "
        "This status is produced by the deterministic Rule Engine and is not generated "
        "or modified by the reporting model."
    )
