from typing import Any

import streamlit as st

from app.ui.components import show_badge


def _rule_results(result: Any) -> list[Any]:
    """Read the deterministic RuleResult objects from the actual workflow result."""
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _status_value(rule: Any) -> str:
    status = getattr(rule, "status", None)
    return str(getattr(status, "value", status or ""))


def _severity_value(rule: Any) -> str:
    severity = getattr(rule, "severity", None)
    return str(getattr(severity, "value", severity or ""))


def _format_value(value: Any) -> str:
    """Format values without assuming that every rule indicator is numeric."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _section_header(title: str, description: str) -> None:
    """Render a consistent visual section header."""
    st.markdown(
        f"""
        <div class="ui-section-header">
            <div class="ui-section-title">{title}</div>
            <div class="ui-section-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_assessment_status(status: str) -> None:
    """Render the assessment status with semantic visual emphasis."""
    normalized = status.upper().replace(" ", "_")
    palette = {
        "CRITICAL": ("#b91c1c", "rgba(185, 28, 28, 0.10)"),
        "ATTENTION": ("#b45309", "rgba(180, 83, 9, 0.10)"),
        "NORMAL": ("#166534", "rgba(22, 101, 52, 0.10)"),
    }
    foreground, background = palette.get(
        normalized,
        ("#4b5563", "rgba(107, 114, 128, 0.10)"),
    )
    label = normalized.replace("_", " ").title()

    st.markdown(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            padding:0.24rem 0.72rem;
            border-radius:999px;
            border:1px solid {foreground}55;
            background:{background};
            color:{foreground};
            font-size:0.78rem;
            font-weight:750;
            letter-spacing:0.02em;
        ">{label}</span>
        """,
        unsafe_allow_html=True,
    )


def _render_driver_highlights(result: Any) -> None:
    """Highlight the first three triggered rules before the full evidence table."""
    triggered = [r for r in _rule_results(result) if _status_value(r) == "TRIGGERED"]
    if not triggered:
        return

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    triggered = sorted(
        triggered,
        key=lambda rule: severity_rank.get(_severity_value(rule).upper(), 99),
    )

    columns = st.columns(min(3, len(triggered)))
    severity_styles = {
        "CRITICAL": ("#b91c1c", "rgba(185, 28, 28, 0.08)"),
        "HIGH": ("#c2410c", "rgba(194, 65, 12, 0.08)"),
        "MEDIUM": ("#b45309", "rgba(180, 83, 9, 0.08)"),
        "LOW": ("#4b5563", "rgba(107, 114, 128, 0.08)"),
    }

    for column, rule in zip(columns, triggered[:3]):
        severity = _severity_value(rule).upper() or "UNKNOWN"
        foreground, background = severity_styles.get(
            severity,
            ("#4b5563", "rgba(107, 114, 128, 0.08)"),
        )
        rule_id = str(getattr(rule, "rule_id", "—"))
        rule_name = str(getattr(rule, "rule_name", "Risk driver"))
        with column:
            st.markdown(
                f"""
                <div style="
                    min-height:112px;
                    padding:0.85rem 0.95rem;
                    border:1px solid {foreground}45;
                    border-left:4px solid {foreground};
                    border-radius:0.75rem;
                    background:{background};
                ">
                    <div style="font-size:0.70rem;color:{foreground};font-weight:750;">
                        {severity}
                    </div>
                    <div style="font-size:0.82rem;font-weight:700;margin-top:0.22rem;">
                        {rule_id}
                    </div>
                    <div style="font-size:0.76rem;line-height:1.35;margin-top:0.18rem;">
                        {rule_name}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_report_source(
    generator_used: str | None,
    selected_reporting_mode: str,
    configured_model: str | None = None,
) -> None:
    """Show the actual generator used for the Executive Report."""
    if generator_used == "FALLBACK":
        show_badge("Deterministic fallback", "fallback")
        st.caption("The selected LLM was unavailable or failed.")
        return

    if generator_used == "PRIMARY" and selected_reporting_mode == "Gemini + Fallback":
        label = "AI-generated — Gemini"
        if configured_model:
            label = f"{label} · {configured_model}"
        show_badge(label, "ai")
        return

    if generator_used == "PRIMARY" and selected_reporting_mode == "Ollama + Fallback":
        label = "AI-generated — Local LLM"
        if configured_model:
            label = f"{label} · {configured_model}"
        show_badge(label, "ai")
        return

    show_badge("Deterministic — Rule Engine", "det")


def render_report_kpis(result: Any) -> None:
    """Render compact KPIs from the actual assessment rule results."""
    rules = _rule_results(result)
    triggered = [r for r in rules if _status_value(r) == "TRIGGERED"]
    critical = [r for r in triggered if _severity_value(r).upper() == "CRITICAL"]
    evaluated = [r for r in rules if _status_value(r) != "NOT_EVALUABLE"]

    report = getattr(result, "report", None)
    status_obj = getattr(report, "assessment_status", None)
    status = str(getattr(status_obj, "value", status_obj or "Not available"))

    columns = st.columns(4)
    values = [
        ("Assessment", status.replace("_", " ").title()),
        ("Rules triggered", len(triggered)),
        ("Critical drivers", len(critical)),
        ("Rules evaluated", len(evaluated)),
    ]
    for column, (label, value) in zip(columns, values):
        with column:
            st.metric(label, value)


def render_key_risk_drivers(result: Any) -> None:
    """Render the highest-priority deterministic risk drivers."""
    triggered = [r for r in _rule_results(result) if _status_value(r) == "TRIGGERED"]

    _section_header(
        "Key Risk Drivers",
        "The highest-priority rules contributing to the credit assessment.",
    )
    if not triggered:
        st.success("No risk rules were triggered by the available financial information.")
        return

    _render_driver_highlights(result)
    st.caption("Complete list of triggered rules")

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    triggered = sorted(
        triggered,
        key=lambda rule: severity_rank.get(_severity_value(rule).upper(), 99),
    )

    rows = []
    for rule in triggered:
        category = getattr(rule, "category", "—")
        category = getattr(category, "value", str(category))
        rows.append(
            {
                "Rule": str(getattr(rule, "rule_id", "—")),
                "Indicator": str(getattr(rule, "rule_name", "—")),
                "Actual": _format_value(getattr(rule, "value", None)),
                "Threshold": _format_value(getattr(rule, "threshold", None)),
                "Severity": _severity_value(rule) or "—",
                "Category": str(category),
            }
        )

    with st.expander("View all triggered rules", expanded=False):
        st.dataframe(rows, use_container_width=True, hide_index=True)


def render_report_findings(result: Any) -> None:
    """Render additional structured findings returned by the Reporting layer."""
    findings = getattr(getattr(result, "report", None), "findings_by_category", None) or []
    if not findings:
        return

    with st.expander("Detailed findings", expanded=False):
        for group in findings:
            category = getattr(group, "category", "Findings")
            category = getattr(category, "value", str(category))
            st.markdown(f"**{str(category).title()}**")
            for finding in getattr(group, "findings", []) or []:
                rule_id = getattr(finding, "rule_id", "Rule")
                severity = getattr(getattr(finding, "severity", None), "value", "")
                label = f"{rule_id} · {severity}" if severity else str(rule_id)
                st.write(f"**{label}** — {getattr(finding, 'text', str(finding))}")


def render_report_limitations(result: Any) -> None:
    """Render limitations returned by the Reporting layer."""
    limitations = getattr(getattr(result, "report", None), "limitations", None) or []
    if not limitations:
        return

    _section_header(
        "Data Limitations",
        "Information gaps that may affect the completeness of the assessment.",
    )
    for limitation in limitations:
        st.write(f"• {getattr(limitation, 'text', str(limitation))}")


def render_execution_metadata(result: Any) -> None:
    """Keep technical provenance available without occupying the main report."""
    metadata = getattr(result, "execution_metadata", None)
    if metadata is None:
        return

    with st.expander("Technical details", expanded=False):
        cols = st.columns(4)
        values = [
            ("Execution ID", getattr(metadata, "execution_id", "—")),
            ("Generator", getattr(metadata, "generator_used", "—") or "—"),
            ("Fallback", "Yes" if getattr(metadata, "fallback_used", False) else "No"),
            ("Total time", f"{getattr(metadata, 'total_elapsed_time', 0.0):.3f} s"),
        ]
        for column, (label, value) in zip(cols, values):
            with column:
                st.caption(label)
                st.write(value)


def render_report_tab(
    result: Any,
    selected_reporting_mode: str,
    report_badge_kind: str,
    report_badge_label: str,
    configured_model: str | None,
) -> None:
    """Render the final Executive Report using the domain result as source of truth."""
    report = getattr(result, "report", None)
    if report is None:
        st.error("The Executive Report is not available for this assessment.")
        return

    generator_used = getattr(result, "report_generator_used", None)
    generation_error = getattr(result, "report_generation_error", None)

    _section_header(
        "Executive Credit Assessment",
        "Final credit judgement and management summary.",
    )

    with st.container(border=True):
        header = st.columns([2, 2, 2])
        status_obj = getattr(report, "assessment_status", None)
        status = str(getattr(status_obj, "value", status_obj or "Not available"))

        with header[0]:
            st.caption("Final assessment")
            _render_assessment_status(status)
        with header[1]:
            st.caption("Report generated by")
            render_report_source(
                generator_used=generator_used,
                selected_reporting_mode=selected_reporting_mode,
                configured_model=configured_model,
            )
        with header[2]:
            st.caption("Position")
            st.write(str(getattr(report, "position_id", "Not available")))

        render_report_kpis(result)

    _section_header(
        "Executive Conclusion",
        "Management-level interpretation of the assessment and its main implications.",
    )
    with st.container(border=True):
        st.markdown(str(getattr(report, "executive_summary", "No executive summary available.")))

    render_key_risk_drivers(result)
    render_report_findings(result)
    render_report_limitations(result)

    if generator_used == "FALLBACK" and generation_error:
        with st.expander("Why fallback was used", expanded=False):
            st.caption(str(generation_error))

    render_execution_metadata(result)
