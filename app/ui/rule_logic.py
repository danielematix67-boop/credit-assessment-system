from typing import Any

import streamlit as st


def _rules(result: Any) -> list[Any]:
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _value(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def _enum_value(value: Any, default: str = "—") -> str:
    return str(getattr(value, "value", value or default))


def _logic(direction: str) -> str:
    if direction == "LOWER_IS_WORSE":
        return "Lower values are worse"
    if direction == "HIGHER_IS_WORSE":
        return "Higher values are worse"
    return "Configured direction"


def render_rule_logic(result: Any) -> None:
    """Explain the configured decision boundary for every evaluated rule."""
    rules = _rules(result)
    if not rules:
        return

    st.markdown("#### Rule Logic & Decision Boundaries")
    st.caption(
        "The Rule Engine compares each indicator with its configured threshold. "
        "The direction defines which side of the boundary represents deterioration."
    )

    rows: list[dict[str, str]] = []
    for rule in rules:
        direction = _enum_value(getattr(rule, "direction", None))
        status = _enum_value(getattr(rule, "status", None))
        severity = _enum_value(getattr(rule, "severity", None))
        rows.append(
            {
                "Rule": str(getattr(rule, "rule_id", "—")),
                "Indicator": str(
                    getattr(rule, "indicator", None)
                    or getattr(rule, "rule_name", "—")
                ),
                "Decision logic": _logic(direction),
                "Threshold": _value(getattr(rule, "threshold", None)),
                "Outcome": status,
                "Severity": severity,
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.caption(
        "Decision boundary interpretation: for LOWER_IS_WORSE indicators, values below "
        "the configured boundary indicate deterioration; for HIGHER_IS_WORSE indicators, "
        "values above the boundary indicate deterioration."
    )
