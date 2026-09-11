"""Presentation helpers for deterministic rule results.

These helpers intentionally read existing RuleResult data only. They do not
recalculate indicators, thresholds, severity, rule status, or assessment status.
"""

from typing import Any

import pandas as pd


def get_rule_sections(result: Any) -> list[Any]:
    """Return the assessment sections from the authoritative credit case."""
    credit_case = getattr(result, "credit_case", None)
    if credit_case is None:
        return []
    return list(getattr(credit_case, "sections", []) or [])


def get_rule_results(result: Any) -> list[Any]:
    """Return deterministic rule evidence across every assessment macro-area."""
    rule_results: list[Any] = []
    for section in get_rule_sections(result):
        rule_results.extend(getattr(section, "evidence", []) or [])
    return rule_results


def build_rule_area_dataframe(result: Any) -> pd.DataFrame:
    """Build rule evidence while preserving the authoritative macro-area name."""
    rows: list[dict[str, Any]] = []
    for section in get_rule_sections(result):
        area = str(getattr(section, "name", "Assessment area"))
        for rule_result in getattr(section, "evidence", []) or []:
            rows.append(
                {
                    "Assessment area": area,
                    "Rule": str(getattr(rule_result, "rule_id", "—")),
                    "Indicator": rule_indicator(rule_result),
                    "Actual": getattr(rule_result, "value", None),
                    "Threshold": getattr(rule_result, "threshold", None),
                    "Status": rule_status(rule_result),
                    "Severity": rule_severity(rule_result),
                    "Category": str(getattr(rule_result, "category", "—")),
                }
            )
    return pd.DataFrame(rows)


def rule_status_counts(result: Any) -> dict[str, int]:
    """Count actual RuleResult statuses without applying business logic."""
    counts = {"TRIGGERED": 0, "NOT_TRIGGERED": 0, "NOT_EVALUABLE": 0}
    for rule_result in get_rule_results(result):
        status = rule_status(rule_result)
        if status in counts:
            counts[status] += 1
    return counts


def rule_status(rule_result: Any) -> str:
    status_obj = getattr(rule_result, "status", None)
    return str(getattr(status_obj, "value", str(status_obj or "—")))


def rule_severity(rule_result: Any) -> str:
    severity_obj = getattr(rule_result, "severity", None)
    return str(getattr(severity_obj, "value", str(severity_obj or "—")))


def severity_rank(severity: str) -> int:
    """Return a display-only severity ranking."""
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(
        severity.upper(), 0
    )


def rule_indicator(rule_result: Any) -> str:
    """Return the explicit deterministic indicator."""
    return str(getattr(rule_result, "indicator", None) or getattr(rule_result, "rule_name", "—"))


def severity_counts(rule_results: list[Any]) -> dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for rule_result in rule_results:
        severity = rule_severity(rule_result).upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def build_rule_dataframe(rule_results: list[Any]) -> pd.DataFrame:
    """Build the dashboard's tabular presentation data from RuleResult objects."""
    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": rule_indicator(rule_result),
                "Actual": getattr(rule_result, "value", None),
                "Threshold": getattr(rule_result, "threshold", None),
                "Status": rule_status(rule_result),
                "Severity": rule_severity(rule_result),
                "Category": str(getattr(rule_result, "category", "—")),
            }
        )
    return pd.DataFrame(rows)


def build_status_overview(status_counts: dict[str, int]) -> pd.DataFrame:
    """Build chart-ready status data without changing the underlying counts."""
    labels = {
        "TRIGGERED": "Triggered",
        "NOT_TRIGGERED": "Not triggered",
        "NOT_EVALUABLE": "Not evaluable",
    }
    return pd.DataFrame(
        {
            "Status": [labels[key] for key in status_counts],
            "Rules": list(status_counts.values()),
        }
    )


def build_severity_overview(severity_counts_data: dict[str, int]) -> pd.DataFrame:
    """Build chart-ready severity data without changing the underlying counts."""
    return pd.DataFrame(
        {
            "Severity": list(severity_counts_data.keys()),
            "Rules": list(severity_counts_data.values()),
        }
    )


def format_indicator_value(value: Any) -> str:
    """Format an already-computed indicator for display only."""
    if value is None:
        return "—"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def status_label(status: str) -> str:
    return {
        "TRIGGERED": "TRIGGERED",
        "NOT_TRIGGERED": "NOT TRIGGERED",
        "NOT_EVALUABLE": "NOT EVALUABLE",
    }.get(status, status.replace("_", " "))


def escape_html(value: Any) -> str:
    """Escape display values before inserting them into presentation HTML."""
    import html

    return html.escape(str(value))
