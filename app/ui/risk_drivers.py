from typing import Any

import streamlit as st


def _rule_results(result: Any) -> list[Any]:
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _value(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def _status(rule: Any) -> str:
    value = getattr(rule, "status", None)
    return str(getattr(value, "value", value or "—"))


def _severity(rule: Any) -> str:
    value = getattr(rule, "severity", None)
    return str(getattr(value, "value", value or "—"))


def _indicator(rule: Any) -> str:
    return str(
        getattr(rule, "indicator", None)
        or getattr(rule, "rule_name", "—")
    )


def render_triggered_risk_drivers(result: Any) -> None:
    """Show triggered deterministic rules as presentation-only risk drivers."""
    triggered = [rule for rule in _rule_results(result) if _status(rule) == "TRIGGERED"]
    if not triggered:
        return

    st.markdown("#### Triggered Risk Drivers")
    st.caption(
        "The rules below are the deterministic risk signals currently triggered by "
        "the Rule Engine. The UI only presents existing RuleResult outputs."
    )

    for rule in triggered:
        rule_id = str(getattr(rule, "rule_id", "—"))
        indicator = _indicator(rule)
        severity = _severity(rule).upper()
        actual = _value(getattr(rule, "value", None))
        threshold = _value(getattr(rule, "threshold", None))
        category = str(getattr(rule, "category", "—"))
        reason = str(getattr(rule, "reason", None) or "No additional rationale provided.")

        severity_class = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
        }.get(severity, "neutral")

        st.markdown(
            f"""
            <div class="risk-driver-card {severity_class}">
                <div class="risk-driver-top">
                    <div>
                        <div class="risk-driver-kicker">{rule_id} · {category}</div>
                        <div class="risk-driver-title">{indicator}</div>
                    </div>
                    <div class="risk-driver-severity">{severity}</div>
                </div>
                <div class="risk-driver-metrics">
                    <div>
                        <span>Actual</span>
                        <strong>{actual}</strong>
                    </div>
                    <div>
                        <span>Threshold</span>
                        <strong>{threshold}</strong>
                    </div>
                    <div>
                        <span>Status</span>
                        <strong>TRIGGERED</strong>
                    </div>
                </div>
                <div class="risk-driver-rationale">
                    <span>Rationale</span>
                    <p>{reason}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    assessment_status = str(getattr(status_obj, "value", status_obj or "Unknown"))
    st.caption(
        f"{len(triggered)} triggered rule(s) currently provide the displayed risk evidence. "
        f"Assessment status: {assessment_status}."
    )
