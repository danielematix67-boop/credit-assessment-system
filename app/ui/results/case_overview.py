from typing import Any

import pandas as pd
import streamlit as st


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status or "NOT_EVALUABLE")).upper()


def _status_class(status: str) -> str:
    return {
        "NORMAL": "normal",
        "ATTENTION": "attention",
        "CRITICAL": "critical",
        "NOT_EVALUABLE": "neutral",
    }.get(status, "neutral")


def _rule_status(rule: Any) -> str:
    return str(getattr(getattr(rule, "status", None), "value", getattr(rule, "status", ""))).upper()


def _indicator_frame(section: Any) -> pd.DataFrame:
    """Build a comparable indicator table without changing deterministic results."""
    rows = []
    for rule in section.evidence:
        value = getattr(rule, "value", None)
        threshold = getattr(rule, "threshold", None)
        if value is None or threshold is None:
            continue
        rows.append(
            {
                "Indicator": getattr(rule, "indicator", getattr(rule, "rule_name", "Indicator")),
                "Value": float(value),
                "Threshold": float(threshold),
                "Status": _rule_status(rule),
                "Rule": getattr(rule, "rule_id", ""),
            }
        )
    return pd.DataFrame(rows)


def _threshold_multiple_frame(section: Any) -> pd.DataFrame:
    """Return value/threshold only where a zero threshold would be meaningful to avoid division errors."""
    frame = _indicator_frame(section)
    if frame.empty:
        return frame
    frame = frame[frame["Threshold"] != 0].copy()
    if frame.empty:
        return frame
    frame["Threshold multiple"] = frame["Value"] / frame["Threshold"]
    return frame.set_index("Indicator")[["Threshold multiple"]]


def _render_financial_chart(section: Any) -> None:
    frame = _threshold_multiple_frame(section)
    if frame.empty:
        return
    st.markdown("**Indicator position vs threshold**")
    st.caption("1.0 = threshold. Values above 1.0 indicate a higher-than-threshold level for these indicators.")
    st.bar_chart(frame, horizontal=True)


def _render_behavioural_chart(section: Any) -> None:
    frame = _threshold_multiple_frame(section)
    if frame.empty:
        return
    st.markdown("**Behavioural indicators vs threshold**")
    st.caption("1.0 = configured threshold; higher values indicate greater behavioural pressure.")
    st.bar_chart(frame, horizontal=True)


def _render_debt_chart(section: Any) -> None:
    frame = _threshold_multiple_frame(section)
    if frame.empty:
        return
    st.markdown("**Debt-service indicators vs threshold**")
    st.caption("1.0 = configured threshold. The cash-flow buffer is shown separately because its threshold is zero.")
    st.bar_chart(frame, horizontal=True)

    buffer_rule = next(
        (rule for rule in section.evidence if getattr(rule, "rule_id", "") == "DS003"),
        None,
    )
    if buffer_rule is not None and getattr(buffer_rule, "value", None) is not None:
        value = float(buffer_rule.value)
        st.metric("Cash Flow Debt-Service Buffer", f"{value:,.2f}")


def _render_final_chart(credit_case: Any) -> None:
    statuses = [_status_value(section.status) for section in credit_case.sections]
    counts = pd.Series(statuses).value_counts().reindex(
        ["NORMAL", "ATTENTION", "CRITICAL", "NOT_EVALUABLE"], fill_value=0
    )
    st.markdown("**Macro-area status distribution**")
    st.bar_chart(counts, horizontal=True)


def _render_section_details(section: Any) -> None:
    """Show evidence and limitations while keeping the decision source deterministic."""
    frame = _indicator_frame(section)
    if not frame.empty:
        display_frame = frame[["Indicator", "Value", "Threshold", "Status", "Rule"]].copy()
        st.dataframe(display_frame, use_container_width=True, hide_index=True)

    if section.findings:
        with st.expander("Triggered findings", expanded=True):
            for finding in section.findings:
                result = getattr(finding, "result", None)
                reason = getattr(result, "reason", None) or getattr(finding, "comment", "")
                st.write(f"• {reason}")

    if section.limitations:
        with st.expander("Limitations", expanded=False):
            for limitation in section.limitations:
                st.write(f"• {limitation}")


def render_credit_analysis_case(result: Any) -> None:
    """Render the analyst-style macro-area view produced by the domain layer."""
    credit_case = getattr(result, "credit_case", None)
    if credit_case is None:
        return

    st.markdown("### Credit Analysis Case")
    st.caption(
        "The assessment is organised into the main analytical areas used in a credit review. "
        "Only implemented areas contribute deterministic evidence; unavailable areas remain explicitly not evaluable."
    )

    sections = credit_case.sections
    cards = []
    for index, section in enumerate(sections, start=1):
        status = _status_value(section.status)
        status_class = _status_class(status)
        evidence_count = len(section.evidence)
        finding_count = len(section.findings)
        cards.append(
            f"""
            <div class="case-section-card">
                <div class="case-section-number">0{index}</div>
                <div class="case-section-name">{section.name}</div>
                <div class="case-section-status {status_class}">{status}</div>
                <div class="case-section-meta">
                    <span>{evidence_count} evidence</span>
                    <span>{finding_count} findings</span>
                </div>
            </div>
            """
        )

    st.markdown(
        """
        <style>
        .case-section-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .75rem;
            margin: .7rem 0 1rem 0;
        }
        .case-section-card {
            min-width: 0;
            padding: 1rem;
            border: 1px solid rgba(128,128,128,.18);
            border-radius: .85rem;
            background: rgba(128,128,128,.025);
        }
        .case-section-number {
            color: rgba(128,128,128,.75);
            font-size: .68rem;
            font-weight: 750;
            letter-spacing: .08em;
        }
        .case-section-name {
            margin-top: .35rem;
            min-height: 2.5rem;
            font-weight: 720;
            line-height: 1.25;
        }
        .case-section-status {
            display: inline-block;
            margin-top: .7rem;
            padding: .28rem .55rem;
            border-radius: 999px;
            font-size: .68rem;
            font-weight: 750;
            letter-spacing: .04em;
        }
        .case-section-status.normal { color: #15803d; background: rgba(21,128,61,.08); }
        .case-section-status.attention { color: #b45309; background: rgba(180,83,9,.09); }
        .case-section-status.critical { color: #b91c1c; background: rgba(185,28,28,.08); }
        .case-section-status.neutral { color: #6b7280; background: rgba(107,114,128,.08); }
        .case-section-meta {
            display: flex;
            justify-content: space-between;
            gap: .5rem;
            margin-top: .75rem;
            color: rgba(128,128,128,.9);
            font-size: .68rem;
        }
        @media (max-width: 900px) {
            .case-section-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        @media (max-width: 560px) {
            .case-section-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="case-section-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("01 · Financial Analysis", expanded=True):
        _render_financial_chart(credit_case.financial_analysis)
        _render_section_details(credit_case.financial_analysis)

    with st.expander("02 · Behavioural Analysis", expanded=True):
        _render_behavioural_chart(credit_case.behavioural_analysis)
        _render_section_details(credit_case.behavioural_analysis)

    with st.expander("03 · Debt Sustainability", expanded=True):
        _render_debt_chart(credit_case.debt_sustainability)
        _render_section_details(credit_case.debt_sustainability)

    final_assessment = getattr(credit_case, "final_assessment", None)
    if final_assessment is not None:
        with st.expander("04 · Final Assessment", expanded=True):
            final_status = _status_value(getattr(final_assessment, "status", None))
            st.info(
                f"Final deterministic aggregation: {final_status}. "
                "This status is calculated by the assessment layer and is not generated by the LLM."
            )
            _render_final_chart(credit_case)
            risk_sections = getattr(final_assessment, "risk_sections", [])
            normal_sections = getattr(final_assessment, "normal_sections", [])
            limitations = getattr(final_assessment, "limitations", [])
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Risk / attention areas", len(risk_sections))
            with col2:
                st.metric("Normal areas", len(normal_sections))
            if limitations:
                with st.expander("Final limitations", expanded=False):
                    for limitation in limitations:
                        st.write(f"• {limitation}")
