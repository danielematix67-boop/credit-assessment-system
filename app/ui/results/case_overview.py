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
    return str(
        getattr(getattr(rule, "status", None), "value", getattr(rule, "status", ""))
    ).upper()


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
                "Indicator": getattr(
                    rule, "indicator", getattr(rule, "rule_name", "Indicator")
                ),
                "Value": float(value),
                "Threshold": float(threshold),
                "Status": _rule_status(rule),
                "Rule": getattr(rule, "rule_id", ""),
            }
        )
    return pd.DataFrame(rows)


def _threshold_distance_frame(section: Any) -> pd.DataFrame:
    """Build a direction-aware distance from threshold for non-zero thresholds."""
    frame = _indicator_frame(section)
    if frame.empty:
        return frame

    rows = []
    for rule in section.evidence:
        value = getattr(rule, "value", None)
        threshold = getattr(rule, "threshold", None)
        direction = getattr(
            getattr(rule, "direction", None),
            "value",
            getattr(rule, "direction", ""),
        )
        if value is None or threshold is None or float(threshold) == 0:
            continue

        value = float(value)
        threshold = float(threshold)
        scale = abs(threshold)
        if direction == "LOWER_IS_WORSE":
            distance = (threshold - value) / scale
        else:
            distance = (value - threshold) / scale

        rows.append(
            {
                "Indicator": getattr(
                    rule, "indicator", getattr(rule, "rule_name", "Indicator")
                ),
                "Threshold distance": distance,
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).set_index("Indicator")


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


def _render_financial_dimensions(section: Any) -> None:
    """Make the deterministic analyst chain visible: dimension -> indicator -> evidence -> finding."""
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
        "Financial indicators are grouped into analytical dimensions to make the analyst reasoning visible. "
        "The dimension view is descriptive only and does not introduce a new risk score or "
        "alter the assessment decision."
    )

    rows = []
    for dimension, rules in dimensions.items():
        rule_list = list(rules or [])
        statuses = [_rule_status(rule) for rule in rule_list]
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
            rule_id = getattr(rule, "rule_id", "")
            detail_rows.append(
                {
                    "Rule": rule_id,
                    "Indicator": getattr(
                        rule, "indicator", getattr(rule, "rule_name", "Indicator")
                    ),
                    "Value": getattr(rule, "value", None),
                    "Threshold": getattr(rule, "threshold", None),
                    "Status": _rule_status(rule),
                }
            )

        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

        for rule in rule_list:
            rule_id = getattr(rule, "rule_id", "")
            if _rule_status(rule) != "TRIGGERED":
                continue
            finding = findings_by_rule.get(rule_id)
            if finding is None:
                continue
            result = getattr(finding, "result", None)
            reason = getattr(result, "reason", None) or getattr(finding, "comment", "")
            if reason:
                indicator = getattr(
                    rule, "indicator", getattr(rule, "rule_name", rule_id)
                )
                st.info(f"**Finding · {indicator} ({rule_id})**\n\n{reason}")


def _render_financial_chart(section: Any) -> None:
    _render_financial_dimensions(section)
    _render_threshold_distance_chart(section, "Indicator position vs threshold")


def _render_behavioural_chart(section: Any) -> None:
    _render_threshold_distance_chart(section, "Behavioural indicators vs threshold")


def _render_debt_chart(section: Any) -> None:
    _render_threshold_distance_chart(section, "Debt-service indicators vs threshold")

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


def _profile_value(data: Any, field: str, default: str = "Not available") -> str:
    if isinstance(data, dict):
        value = data.get(field)
    else:
        value = getattr(data, field, None)
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _profile_completeness(data: Any) -> tuple[int, int]:
    fields = (
        "company_name",
        "legal_form",
        "sector",
        "size_class",
        "geography",
        "relationship_years",
        "historical_facilities",
        "active_ews",
        "previous_restructuring",
    )
    available = sum(
        _profile_value(data, field, "") != ""
        and _profile_value(data, field, "") != "Not available"
        for field in fields
    )
    return available, len(fields)


def _profile_list(data: Any, field: str) -> list[Any]:
    if isinstance(data, dict):
        value = data.get(field, [])
    else:
        value = getattr(data, field, [])
    return list(value or [])


def _render_customer_profile(section: Any) -> None:
    """Render descriptive customer context without introducing a synthetic risk score."""
    context = getattr(section, "context", {}) or {}
    if not context:
        st.info("Customer profile information is not available.")
        return

    available, total = _profile_completeness(context)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Profile information", f"{available}/{total}")
    with col2:
        relationship_years = _profile_value(context, "relationship_years", "—")
        st.metric("Banking relationship", f"{relationship_years} years")
    with col3:
        st.metric(
            "Historical facilities",
            len(_profile_list(context, "historical_facilities")),
        )

    st.markdown("**Company & anagraphic profile**")
    profile_frame = pd.DataFrame(
        [
            {
                "Company": _profile_value(context, "company_name"),
                "Legal form": _profile_value(context, "legal_form"),
                "Sector": _profile_value(context, "sector"),
                "Size class": _profile_value(context, "size_class"),
                "Geography": _profile_value(context, "geography"),
            }
        ]
    )
    st.dataframe(profile_frame, use_container_width=True, hide_index=True)

    relationship_col, ownership_col = st.columns(2)
    with relationship_col:
        st.markdown("**Banking relationship**")
        facilities = _profile_list(context, "historical_facilities")
        if facilities:
            st.write("Historical facilities")
            for facility in facilities:
                st.write(f"• {facility}")
        else:
            st.caption("No historical facility information available.")

    with ownership_col:
        st.markdown("**Ownership & management**")
        shareholders = _profile_list(context, "shareholders")
        management = _profile_list(context, "management_members")
        if shareholders:
            st.write("Shareholders")
            for shareholder in shareholders:
                st.write(f"• {shareholder}")
        if management:
            st.write("Management")
            for member in management:
                st.write(f"• {member}")
        if not shareholders and not management:
            st.caption("Ownership and management information not available.")

    st.markdown("**Risk-context signals**")
    evidence_by_rule = {getattr(rule, "rule_id", ""): rule for rule in section.evidence}
    signal_frame = pd.DataFrame(
        [
            {
                "Signal": "Active EWS",
                "Value": _rule_status(evidence_by_rule["CP001"])
                if "CP001" in evidence_by_rule
                else "NOT_EVALUABLE",
            },
            {
                "Signal": "Previous restructuring",
                "Value": _rule_status(evidence_by_rule["CP002"])
                if "CP002" in evidence_by_rule
                else "NOT_EVALUABLE",
            },
        ]
    )
    st.dataframe(signal_frame, use_container_width=True, hide_index=True)


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


def _render_data_quality_overview(credit_case: Any) -> None:
    """Show evidence coverage and data limitations before interpreting risk."""
    sections = list(getattr(credit_case, "sections", []) or [])
    total_evidence = sum(
        len(getattr(section, "evidence", []) or []) for section in sections
    )
    evaluable_evidence = sum(
        sum(
            _rule_status(rule) != "NOT_EVALUABLE"
            for rule in getattr(section, "evidence", [])
        )
        for section in sections
    )
    not_evaluable_evidence = total_evidence - evaluable_evidence
    sections_with_limitations = sum(
        bool(getattr(section, "limitations", [])) for section in sections
    )
    coverage = evaluable_evidence / total_evidence if total_evidence else 0.0

    st.markdown("### Data & Evidence Quality")
    st.caption(
        "Evidence coverage is shown separately from credit risk. Missing or unavailable data are "
        "explicit limitations and do not become a synthetic risk score."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Evidence items", total_evidence)
    with col2:
        st.metric("Evaluable", evaluable_evidence)
    with col3:
        st.metric("Not evaluable", not_evaluable_evidence)
    with col4:
        st.metric("Evidence coverage", f"{coverage:.0%}")

    quality_rows = []
    for section in sections:
        evidence = list(getattr(section, "evidence", []) or [])
        total = len(evidence)
        evaluable = sum(_rule_status(rule) != "NOT_EVALUABLE" for rule in evidence)
        quality_rows.append(
            {
                "Macro-area": section.name,
                "Evidence": total,
                "Evaluable": evaluable,
                "Not evaluable": total - evaluable,
                "Coverage": evaluable / total if total else 0.0,
                "Limitations": len(getattr(section, "limitations", []) or []),
            }
        )

    quality_frame = pd.DataFrame(quality_rows)
    if quality_frame.empty:
        st.info("No evidence items are available for this case.")
        return

    chart_frame = quality_frame.set_index("Macro-area")[["Evaluable", "Not evaluable"]]
    st.bar_chart(chart_frame, horizontal=True)

    display_frame = quality_frame.copy()
    display_frame["Coverage"] = display_frame["Coverage"].map(lambda value: f"{value:.0%}")
    st.dataframe(display_frame, use_container_width=True, hide_index=True)

    if sections_with_limitations:
        st.info(
            f"{sections_with_limitations} of {len(sections)} macro-areas contain explicit data limitations. "
            "Review these limitations before interpreting the final assessment."
        )


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

    _render_data_quality_overview(credit_case)

    sections = credit_case.sections
    for section in sections:
        status = _status_value(section.status)
        status_class = _status_class(status)
        st.markdown(
            f"### {section.name} "
            f"<span class='status-badge {status_class}'>{status}</span>",
            unsafe_allow_html=True,
        )

        if section.name == "Financial Analysis":
            _render_financial_chart(section)
        elif section.name == "Behavioural Analysis":
            _render_behavioural_chart(section)
        elif section.name == "Debt Sustainability":
            _render_debt_chart(section)
        elif section.name == "Customer Profile":
            _render_customer_profile(section)

        _render_section_details(section)

    _render_final_chart(credit_case)
