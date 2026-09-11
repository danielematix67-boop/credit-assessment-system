from types import SimpleNamespace

from app.ui.results.risk_drivers import build_risk_driver_frame


def _rule(
    rule_id: str,
    value: float | None,
    threshold: float | None,
    status: str,
    indicator: str,
    severity: str = "HIGH",
) -> SimpleNamespace:
    return SimpleNamespace(
        rule_id=rule_id,
        value=value,
        threshold=threshold,
        status=status,
        indicator=indicator,
        severity=severity,
    )


def test_build_risk_driver_frame_keeps_only_triggered_rules() -> None:
    credit_case = SimpleNamespace(
        sections=[
            SimpleNamespace(
                name="Financial Analysis",
                evidence=[
                    _rule("R001", -0.20, -0.10, "TRIGGERED", "Revenue Growth"),
                    _rule("R003", 3.00, 5.00, "NOT_TRIGGERED", "NFP / EBITDA"),
                ],
            ),
            SimpleNamespace(
                name="Debt Sustainability",
                evidence=[
                    _rule("DS001", 0.80, 1.00, "TRIGGERED", "Debt Service Coverage"),
                ],
            ),
        ]
    )

    frame = build_risk_driver_frame(credit_case)

    assert list(frame["Rule"]) == ["R001", "DS001"]
    assert list(frame["Macro-area"]) == [
        "Financial Analysis",
        "Debt Sustainability",
    ]
    assert list(frame.columns) == [
        "Macro-area",
        "Rule",
        "Indicator",
        "Actual",
        "Threshold",
        "Severity",
    ]
    assert "Distance" not in frame.columns
    assert "Relation" not in frame.columns


def test_build_risk_driver_frame_sorts_by_existing_severity() -> None:
    credit_case = SimpleNamespace(
        sections=[
            SimpleNamespace(
                name="Financial Analysis",
                evidence=[
                    _rule("R001", -0.20, -0.10, "TRIGGERED", "Revenue Growth", "HIGH"),
                    _rule("R002", 0.05, 0.00, "TRIGGERED", "EBITDA Margin", "CRITICAL"),
                    _rule("R003", 7.00, 5.00, "TRIGGERED", "NFP / EBITDA", "MEDIUM"),
                ],
            )
        ]
    )

    frame = build_risk_driver_frame(credit_case)

    assert list(frame["Rule"]) == ["R002", "R001", "R003"]
    assert list(frame["Severity"]) == ["CRITICAL", "HIGH", "MEDIUM"]


def test_build_risk_driver_frame_preserves_actual_and_threshold() -> None:
    credit_case = SimpleNamespace(
        sections=[
            SimpleNamespace(
                name="Financial Analysis",
                evidence=[
                    _rule("R002", 0.05, 0.00, "TRIGGERED", "EBITDA Margin"),
                ],
            )
        ]
    )

    frame = build_risk_driver_frame(credit_case)

    assert frame.loc[0, "Actual"] == 0.05
    assert frame.loc[0, "Threshold"] == 0.00
