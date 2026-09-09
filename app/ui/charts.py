from typing import Any

import pandas as pd
import streamlit as st

# ============================================================
# Shared Rule Result Helpers
# ============================================================


def _get_rule_results(result: Any) -> list[Any]:
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _rule_status_counts(result: Any) -> dict[str, int]:
    """Count actual RuleResult statuses without applying business logic."""
    counts = {"TRIGGERED": 0, "NOT_TRIGGERED": 0, "NOT_EVALUABLE": 0}
    for rule_result in _get_rule_results(result):
        status = getattr(getattr(rule_result, "status", None), "value", "")
        if status in counts:
            counts[status] += 1
    return counts


def _rule_status(rule_result: Any) -> str:
    status_obj = getattr(rule_result, "status", None)
    return str(getattr(status_obj, "value", str(status_obj or "—")))


def _rule_severity(rule_result: Any) -> str:
    severity_obj = getattr(rule_result, "severity", None)
    return str(getattr(severity_obj, "value", str(severity_obj or "—")))


def _rule_direction(rule_result: Any) -> str:
    direction_obj = getattr(rule_result, "direction", None)
    return str(getattr(direction_obj, "value", str(direction_obj or "—")))


def _severity_rank(severity: str) -> int:
    """Return a display-only severity ranking."""
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(
        severity.upper(), 0
    )


def _rule_indicator(rule_result: Any) -> str:
    """Return the explicit deterministic indicator, with legacy fallback."""
    return str(
        getattr(rule_result, "indicator", None)
        or getattr(rule_result, "rule_name", "—")
    )


def _severity_counts(rule_results: list[Any]) -> dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for rule_result in rule_results:
        severity = _rule_severity(rule_result).upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def _format_indicator_value(value: Any) -> str:
    """Format an already-computed indicator for display only."""
    if value is None:
        return "—"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def _status_label(status: str) -> str:
    return {
        "TRIGGERED": "TRIGGERED",
        "NOT_TRIGGERED": "NOT TRIGGERED",
        "NOT_EVALUABLE": "NOT EVALUABLE",
    }.get(status, status.replace("_", " "))


def _escape_html(value: Any) -> str:
    """Escape display values before inserting them into presentation HTML."""
    import html

    return html.escape(str(value))


# ============================================================
# Decision Path
# ============================================================


def render_decision_path(result: Any) -> None:
    """Explain visually how deterministic rule outcomes lead to the assessment."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    assessment_status = str(
        getattr(status_obj, "value", str(status_obj or "Unknown"))
    )
    counts = _rule_status_counts(result)
    triggered_rules = [
        rule_result
        for rule_result in rule_results
        if _rule_status(rule_result) == "TRIGGERED"
    ]
    not_evaluable = counts["NOT_EVALUABLE"]

    st.subheader("How the Decision Is Produced")
    st.caption(
        "A transparent view of how the deterministic Rule Engine converts financial "
        "indicators into risk evidence and the final monitoring judgement."
    )

    st.markdown(
        """
        <style>
        .decision-flow {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1.25fr) 42px minmax(0, 1fr);
            align-items: stretch;
            gap: .45rem;
            margin: .55rem 0 .85rem 0;
        }
        .decision-node {
            min-width: 0;
            padding: 1rem 1.05rem;
            border: 1px solid rgba(128,128,128,.20);
            border-radius: .85rem;
            background: rgba(128,128,128,.025);
        }
        .decision-node.det {
            border-color: rgba(37,99,235,.30);
            background: rgba(37,99,235,.055);
        }
        .decision-node.result {
            border-color: rgba(185,28,28,.25);
            background: rgba(185,28,28,.045);
        }
        .decision-node-kicker {
            color: rgba(128,128,128,.95);
            font-size: .68rem;
            font-weight: 750;
            letter-spacing: .09em;
            text-transform: uppercase;
        }
        .decision-node-title {
            margin-top: .2rem;
            font-size: .98rem;
            font-weight: 730;
            line-height: 1.25;
        }
        .decision-node-value {
            margin-top: .45rem;
            font-size: 1.45rem;
            font-weight: 780;
            line-height: 1.1;
        }
        .decision-node-description {
            margin-top: .35rem;
            color: rgba(128,128,128,.95);
            font-size: .76rem;
            line-height: 1.4;
        }
        .decision-arrow {
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(128,128,128,.85);
            font-size: 1.25rem;
            font-weight: 650;
        }
        .decision-evidence {
            display: flex;
            flex-wrap: wrap;
            gap: .35rem;
            margin-top: .65rem;
        }
        .decision-chip {
            display: inline-flex;
            align-items: center;
            gap: .3rem;
            padding: .24rem .52rem;
            border-radius: 999px;
            border: 1px solid rgba(185,28,28,.18);
            background: rgba(185,28,28,.065);
            font-size: .70rem;
            font-weight: 650;
        }
        .decision-chip-muted {
            border-color: rgba(128,128,128,.18);
            background: rgba(128,128,128,.045);
        }
        .decision-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin: .15rem 0 .35rem 0;
            color: rgba(128,128,128,.95);
            font-size: .74rem;
        }
        @media (max-width: 760px) {
            .decision-flow {
                grid-template-columns: 1fr;
            }
            .decision-arrow {
                transform: rotate(90deg);
                min-height: 22px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    evidence_chips = "".join(
        f'<span class="decision-chip">{_escape_html(getattr(rule, "rule_id", "—"))} · '
        f'{_escape_html(_rule_indicator(rule))} · {_escape_html(_rule_severity(rule))}</span>'
        for rule in triggered_rules
    )
    if not evidence_chips:
        evidence_chips = (
            '<span class="decision-chip decision-chip-muted">'
            "No triggered rules"
            "</span>"
        )

    status_class = "result" if assessment_status.upper() == "CRITICAL" else "det"
    decision_flow = f"""
        <div class="decision-flow">
            <div class="decision-node det">
                <div class="decision-node-kicker">01 · Inputs</div>
                <div class="decision-node-title">Financial Indicators</div>
                <div class="decision-node-value">{len(rule_results)}</div>
                <div class="decision-node-description">
                    Deterministic indicators evaluated from the credit position.
                </div>
            </div>
            <div class="decision-arrow">→</div>
            <div class="decision-node det">
                <div class="decision-node-kicker">02 · Evidence</div>
                <div class="decision-node-title">Rule Engine Outcomes</div>
                <div class="decision-node-value">{len(triggered_rules)} triggered</div>
                <div class="decision-node-description">
                    Triggered rules provide the factual risk evidence used by the assessment.
                </div>
                <div class="decision-evidence">{evidence_chips}</div>
            </div>
            <div class="decision-arrow">→</div>
            <div class="decision-node {status_class}">
                <div class="decision-node-kicker">03 · Judgement</div>
                <div class="decision-node-title">Monitoring Assessment</div>
                <div class="decision-node-value">{_escape_html(assessment_status)}</div>
                <div class="decision-node-description">
                    Final status returned by the deterministic assessment engine.
                </div>
            </div>
        </div>
        <div class="decision-legend">
            <span>● Deterministic Rule Engine</span>
            <span>● Triggered rules = risk evidence</span>
            <span>● Not evaluable indicators: {not_evaluable}</span>
        </div>
    """
    st.markdown(decision_flow, unsafe_allow_html=True)

    st.caption(
        "The flow is explanatory only: it visualises existing RuleResult outputs and "
        "does not recalculate thresholds, severity or assessment status."
    )


# ============================================================
# Rule Evidence Matrix
# ============================================================


def render_rule_evidence_matrix(result: Any) -> None:
    """Show a compact, display-only matrix of deterministic rule evidence."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    st.markdown("#### Rule Evidence Matrix")
    st.caption(
        "The matrix shows how each deterministic indicator is evaluated against its "
        "configured threshold and records the resulting rule outcome."
    )

    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": _rule_indicator(rule_result),
                "Actual": _format_indicator_value(getattr(rule_result, "value", None)),
                "Threshold": _format_indicator_value(
                    getattr(rule_result, "threshold", None)
                ),
                "Status": _status_label(_rule_status(rule_result)),
                "Severity": _rule_severity(rule_result),
            }
        )

    matrix = pd.DataFrame(rows)
    st.dataframe(
        matrix,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rule": st.column_config.TextColumn("Rule", width="small"),
            "Indicator": st.column_config.TextColumn("Indicator", width="medium"),
            "Actual": st.column_config.TextColumn("Actual", width="small"),
            "Threshold": st.column_config.TextColumn("Threshold", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
        },
    )
    st.caption(
        "Presentation-only evidence view. Values, thresholds, status and severity are "
        "read directly from RuleResult and are not recalculated by the UI."
    )


# ============================================================
# Risk Indicator Dashboard
# ============================================================


def render_risk_indicator_dashboard(result: Any) -> None:
    """Render the complete rule-outcome and indicator diagnostic dashboard."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    st.subheader("Risk Indicator Dashboard")
    st.caption(
        "A structured view of the deterministic indicators, rule outcomes and risk severity."
    )

    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": _rule_indicator(rule_result),
                "Actual": getattr(rule_result, "value", None),
                "Threshold": getattr(rule_result, "threshold", None),
                "Status": _rule_status(rule_result),
                "Severity": _rule_severity(rule_result),
                "Category": str(getattr(rule_result, "category", "—")),
            }
        )

    dataframe = pd.DataFrame(rows)
    status_counts = _rule_status_counts(result)
    severity_counts = _severity_counts(rule_results)

    metric_cols = st.columns(4)
    metrics = [
        ("Indicators", len(rule_results)),
        ("Triggered", status_counts["TRIGGERED"]),
        ("High / critical", severity_counts["HIGH"] + severity_counts["CRITICAL"]),
        ("Not evaluable", status_counts["NOT_EVALUABLE"]),
    ]
    for column, (label, value) in zip(metric_cols, metrics):
        with column:
            st.metric(label, value)

    # Presentation-only decision bridge. Every value is derived from the
    # existing RuleResult collection and deterministic assessment status.
    st.markdown("#### Assessment Decision Bridge")
    st.caption(
        "A compact visual bridge between evaluated indicators, rule outcomes and the "
        "final deterministic monitoring assessment."
    )

    bridge_cols = st.columns([1, 0.22, 1, 0.22, 1])
    assessment = getattr(result, "assessment", None)
    assessment_status = str(
        getattr(getattr(assessment, "status", None), "value", "Unknown")
    )
    bridge_items = [
        ("Indicators evaluated", str(len(rule_results)), "Financial evidence"),
        ("Rules triggered", str(status_counts["TRIGGERED"]), "Risk evidence"),
        ("Final assessment", assessment_status, "Deterministic judgement"),
    ]

    for card_index, (label, value, description) in zip((0, 2, 4), bridge_items):
        with bridge_cols[card_index]:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"### {value}")
                st.caption(description)

    for arrow_index in (1, 3):
        with bridge_cols[arrow_index]:
            st.markdown(
                "<div style='text-align:center; padding-top:2.1rem; "
                "font-size:1.3rem;'>→</div>",
                unsafe_allow_html=True,
            )

    bridge_meta = st.columns(3)
    bridge_meta[0].caption(f"{len(rule_results)} indicators evaluated")
    bridge_meta[1].caption(
        f"{status_counts['TRIGGERED']} of {len(rule_results)} rules triggered"
    )
    bridge_meta[2].caption(
        f"{severity_counts['HIGH'] + severity_counts['CRITICAL']} "
        "high/critical severity outcomes"
    )
    st.caption(
        "This bridge is explanatory only. It does not recalculate thresholds, severity "
        "or assessment status."
    )

    st.markdown("#### Risk Signal Overview")
    overview_cols = st.columns(2)
    with overview_cols[0]:
        labels = {
            "TRIGGERED": "Triggered",
            "NOT_TRIGGERED": "Not triggered",
            "NOT_EVALUABLE": "Not evaluable",
        }
        status_data = pd.DataFrame(
            {
                "Status": [labels[key] for key in status_counts],
                "Rules": list(status_counts.values()),
            }
        )
        st.caption("Rule outcomes")
        st.bar_chart(status_data, x="Status", y="Rules", horizontal=True, height=190)

    with overview_cols[1]:
        severity_data = pd.DataFrame(
            {
                "Severity": list(severity_counts.keys()),
                "Rules": list(severity_counts.values()),
            }
        )
        st.caption("Severity profile")
        st.bar_chart(severity_data, x="Severity", y="Rules", horizontal=True, height=190)

    st.caption(
        "Both views describe the factual Rule Engine output; they do not recalculate the assessment."
    )

    render_rule_evidence_matrix(result)

    st.markdown("#### Rule Catalogue")
    st.caption("Filter the complete rule set before inspecting individual rule evidence.")

    filter_cols = st.columns([1.2, 1.2, 1.6, 1.4])
    with filter_cols[0]:
        status_options = ["All", "TRIGGERED", "NOT_TRIGGERED", "NOT_EVALUABLE"]
        selected_status = st.selectbox(
            "Status",
            status_options,
            index=1 if status_counts["TRIGGERED"] else 0,
            key="rule_catalogue_status",
        )

    with filter_cols[1]:
        severity_values = sorted(
            {
                str(value)
                for value in dataframe["Severity"].dropna().tolist()
                if str(value) not in {"", "—"}
            },
            key=_severity_rank,
            reverse=True,
        )
        selected_severity = st.selectbox(
            "Severity",
            ["All", *severity_values],
            key="rule_catalogue_severity",
        )

    with filter_cols[2]:
        categories = sorted(
            {
                str(value)
                for value in dataframe["Category"].dropna().tolist()
                if str(value) not in {"", "—"}
            }
        )
        selected_category = st.selectbox(
            "Category",
            ["All", *categories],
            key="rule_catalogue_category",
        )

    with filter_cols[3]:
        selected_sort = st.selectbox(
            "Sort by",
            ["Priority", "Rule ID", "Category", "Status"],
            key="rule_catalogue_sort",
        )

    filtered = dataframe.copy()
    if selected_status != "All":
        filtered = filtered[filtered["Status"] == selected_status]
    if selected_severity != "All":
        filtered = filtered[filtered["Severity"] == selected_severity]
    if selected_category != "All":
        filtered = filtered[filtered["Category"] == selected_category]

    filtered["_priority"] = filtered.apply(
        lambda row: (
            0 if row["Status"] == "TRIGGERED" else 1,
            -_severity_rank(str(row["Severity"])),
            str(row["Rule"]),
        ),
        axis=1,
    )

    if selected_sort == "Priority":
        filtered = filtered.sort_values("_priority", ascending=True)
    elif selected_sort == "Rule ID":
        filtered = filtered.sort_values("Rule", ascending=True)
    elif selected_sort == "Category":
        filtered = filtered.sort_values(["Category", "Rule"], ascending=True)
    else:
        filtered = filtered.sort_values(["Status", "Rule"], ascending=True)

    total_filtered = len(filtered)
    st.caption(f"Showing {total_filtered} of {len(dataframe)} evaluated rules.")
    display_columns = [
        "Rule",
        "Indicator",
        "Actual",
        "Threshold",
        "Status",
        "Severity",
        "Category",
    ]

    with st.expander("View filtered rule results", expanded=total_filtered <= 20):
        if filtered.empty:
            st.info("No rules match the selected filters.")
        else:
            st.dataframe(
                filtered[display_columns],
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Inspect individual rule detail", expanded=True):
        render_rule_indicator_detail(result)


# ============================================================
# Rule Indicator Detail
# ============================================================


def render_rule_indicator_detail(result: Any) -> None:
    """Render a professional, display-only risk indicator card."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    st.markdown("##### Risk Indicator Detail")
    st.caption(
        "Inspect the deterministic Rule Engine output for one indicator, including "
        "the observed value, configured threshold and resulting status."
    )

    rule_labels = []
    for rule_result in rule_results:
        rule_id = str(getattr(rule_result, "rule_id", ""))
        rule_name = str(getattr(rule_result, "rule_name", ""))
        label = f"{rule_id} — {rule_name}" if rule_name else rule_id
        rule_labels.append(label)

    triggered_indices = [
        index
        for index, rule_result in enumerate(rule_results)
        if _rule_status(rule_result) == "TRIGGERED"
    ]
    default_index = triggered_indices[0] if triggered_indices else 0

    selected_label = st.selectbox(
        "Indicator",
        rule_labels,
        index=default_index,
        key="rule_indicator_detail",
    )
    selected_index = rule_labels.index(selected_label)
    selected_rule = rule_results[selected_index]

    rule_id = str(getattr(selected_rule, "rule_id", "—"))
    rule_name = str(getattr(selected_rule, "rule_name", "—"))
    indicator = _rule_indicator(selected_rule)
    category = str(getattr(selected_rule, "category", "—"))
    status = _rule_status(selected_rule)
    severity = _rule_severity(selected_rule)
    direction = _rule_direction(selected_rule)
    value = getattr(selected_rule, "value", None)
    threshold = getattr(selected_rule, "threshold", None)
    reason = getattr(selected_rule, "reason", None)

    status_text = _status_label(status)
    severity_text = severity.upper()

    # Presentation-only card. All displayed values come directly from RuleResult.
    with st.container(border=True):
        header_cols = st.columns([4.5, 1.5])
        with header_cols[0]:
            st.caption(f"{rule_id}  ·  {category}")
            st.markdown(f"### {indicator}")
            if rule_name and rule_name != indicator:
                st.caption(rule_name)
        with header_cols[1]:
            st.metric("Risk level", severity_text)

        value_cols = st.columns(2)
        with value_cols[0]:
            st.caption("Observed value")
            st.markdown(f"## {_format_indicator_value(value)}")
        with value_cols[1]:
            st.caption("Configured threshold")
            st.markdown(f"## {_format_indicator_value(threshold)}")

        if value is not None and threshold is not None:
            chart_data = pd.DataFrame(
                {
                    "Measure": ["Actual", "Threshold"],
                    "Value": [float(value), float(threshold)],
                }
            )
            st.bar_chart(chart_data, x="Measure", y="Value", height=170)

        meta_cols = st.columns(3)
        with meta_cols[0]:
            st.caption("Status")
            st.markdown(f"**{status_text}**")
        with meta_cols[1]:
            st.caption("Direction")
            st.markdown(f"**{direction}**")
        with meta_cols[2]:
            st.caption("Category")
            st.markdown(f"**{category}**")

        if reason:
            st.markdown("**Rationale**")
            st.write(reason)

    st.caption(
        "The card presents the Rule Engine output as-is; it does not recalculate "
        "thresholds, severity or assessment status."
    )
