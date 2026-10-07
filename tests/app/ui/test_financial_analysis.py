from types import SimpleNamespace

from app.ui.results.financial_analysis import (
    build_indicator_analysis_frame,
    build_operating_leverage_frame,
)


def _rule(
    rule_id: str,
    value: float | None,
    threshold: float | None,
    status: str,
    indicator: str,
    severity: str = "MEDIUM",
) -> SimpleNamespace:
    return SimpleNamespace(
        rule_id=rule_id,
        value=value,
        threshold=threshold,
        status=status,
        indicator=indicator,
        severity=severity,
    )


def test_indicator_analysis_frame_exposes_deterministic_evidence() -> None:
    section = SimpleNamespace(
        evidence=[
            _rule("R001", -0.20, -0.10, "TRIGGERED", "Revenue Growth"),
            _rule("R002", 0.05, 0.00, "TRIGGERED", "EBITDA Margin"),
            _rule("R003", 3.00, 5.00, "NOT_TRIGGERED", "NFP / EBITDA"),
            _rule("R004", None, 2.00, "NOT_EVALUABLE", "Interest Coverage"),
        ]
    )

    frame = build_indicator_analysis_frame(section)

    assert list(frame.columns) == ["Rule", "Indicator", "Value", "Threshold", "Status"]
    assert list(frame["Rule"]) == ["R001", "R002", "R003"]
    assert frame.loc[0, "Value"] == -0.20
    assert frame.loc[0, "Threshold"] == -0.10
    assert frame.loc[0, "Status"] == "TRIGGERED"


def test_operating_leverage_frame_exposes_r008_ratio() -> None:
    section = SimpleNamespace(
        evidence=[
            _rule(
                "R008",
                4.0,
                3.0,
                "TRIGGERED",
                "Contribution margin / EBIT",
                "MEDIUM",
            )
        ]
    )

    frame = build_operating_leverage_frame(section)

    assert list(frame.columns) == [
        "Indicator",
        "Ratio",
        "Trigger threshold",
        "Status",
        "Severity",
    ]
    assert frame.loc[0, "Ratio"] == 4.0
    assert frame.loc[0, "Trigger threshold"] == 3.0
    assert frame.loc[0, "Status"] == "TRIGGERED"
    assert frame.loc[0, "Severity"] == "MEDIUM"
