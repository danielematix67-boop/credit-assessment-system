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


def test_build_risk_driver_frame_shows_triggered_rules_across_sections() -> None:
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
                    _rule("DS001", 0.80, 1.00, "TRIGGERED", "Debt Service Coverage")
                ],
            ),
        ]
    )

    frame = build_risk_driver_frame(credit_case)

    assert list(frame.columns) == [
        "Macro-area",
        "Rule",
        "Indicator",
        "Value",
        "Threshold",
        "Status",
        "Severity",
    ]
    assert list(frame["Rule"]) == ["DS001", "R001"]
    assert list(frame["Macro-area"]) == [
        "Debt Sustainability",
        "Financial Analysis",
    ]
    assert list(frame["Status"]) == ["TRIGGERED", "TRIGGERED"]
    assert list(frame["Value"]) == [0.80, -0.20]
    assert list(frame["Threshold"]) == [1.00, -0.10]


def test_build_risk_driver_frame_returns_empty_for_no_triggered_rules() -> None:
    credit_case = SimpleNamespace(
        sections=[
            SimpleNamespace(
                name="Financial Analysis",
                evidence=[_rule("R003", 3.00, 5.00, "NOT_TRIGGERED", "NFP / EBITDA")],
            )
        ]
    )

    frame = build_risk_driver_frame(credit_case)

    assert frame.empty
    assert list(frame.columns) == []
