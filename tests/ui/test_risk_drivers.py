from types import SimpleNamespace

import pandas as pd
import pytest

from app.ui.results.risk_drivers import (
    _threshold_distance,
    build_risk_driver_frame,
)


def _rule(
    rule_id: str,
    value: float | None,
    threshold: float | None,
    status: str,
    direction: str,
    indicator: str,
    severity: str = "HIGH",
) -> SimpleNamespace:
    return SimpleNamespace(
        rule_id=rule_id,
        value=value,
        threshold=threshold,
        status=status,
        direction=direction,
        indicator=indicator,
        severity=severity,
    )


def test_threshold_distance_positive_means_worse() -> None:
    assert _threshold_distance(-0.20, -0.10, "LOWER_IS_WORSE") == pytest.approx(1.0)
    assert _threshold_distance(7.0, 5.0, "HIGHER_IS_WORSE") == pytest.approx(0.4)


def test_build_risk_driver_frame_ranks_triggered_rules_across_sections() -> None:
    credit_case = SimpleNamespace(
        sections=[
            SimpleNamespace(
                name="Financial Analysis",
                evidence=[
                    _rule(
                        "R001",
                        -0.20,
                        -0.10,
                        "TRIGGERED",
                        "LOWER_IS_WORSE",
                        "Revenue Growth",
                    ),
                    _rule(
                        "R003",
                        3.00,
                        5.00,
                        "NOT_TRIGGERED",
                        "HIGHER_IS_WORSE",
                        "NFP / EBITDA",
                    ),
                ],
            ),
            SimpleNamespace(
                name="Debt Sustainability",
                evidence=[
                    _rule(
                        "DS001",
                        0.80,
                        1.00,
                        "TRIGGERED",
                        "LOWER_IS_WORSE",
                        "Debt Service Coverage",
                    )
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
    assert frame.loc[0, "Distance"] == pytest.approx(1.0)
    assert frame.loc[1, "Distance"] == pytest.approx(0.2)
    assert set(frame["Relation"]) == {"Worse than threshold"}


def test_build_risk_driver_frame_keeps_zero_threshold_triggered_rules() -> None:
    credit_case = SimpleNamespace(
        sections=[
            SimpleNamespace(
                name="Financial Analysis",
                evidence=[
                    _rule(
                        "R002",
                        0.05,
                        0.00,
                        "TRIGGERED",
                        "LOWER_IS_WORSE",
                        "EBITDA Margin",
                    )
                ],
            )
        ]
    )

    frame = build_risk_driver_frame(credit_case)

    assert len(frame) == 1
    assert frame.loc[0, "Relation"] == "Threshold = 0"
    assert pd.isna(frame.loc[0, "Distance"])
