from types import SimpleNamespace

import pandas as pd
import pytest

from app.ui.results.financial_analysis import build_indicator_analysis_frame
from app.ui.results.helpers import threshold_distance


def _rule(
    rule_id: str,
    value: float | None,
    threshold: float | None,
    status: str,
    direction: str,
    indicator: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        rule_id=rule_id,
        value=value,
        threshold=threshold,
        status=status,
        direction=direction,
        indicator=indicator,
    )


def test_threshold_distance_positive_means_worse_for_lower_is_worse() -> None:
    assert threshold_distance(0.0, 2.0, "LOWER_IS_WORSE") == pytest.approx(1.0)
    assert threshold_distance(3.0, 2.0, "LOWER_IS_WORSE") == pytest.approx(-0.5)


def test_threshold_distance_positive_means_worse_for_higher_is_worse() -> None:
    assert threshold_distance(7.0, 5.0, "HIGHER_IS_WORSE") == pytest.approx(0.4)
    assert threshold_distance(4.0, 5.0, "HIGHER_IS_WORSE") == pytest.approx(-0.2)


def test_threshold_distance_is_not_normalized_when_threshold_is_zero() -> None:
    assert threshold_distance(-0.1, 0.0, "LOWER_IS_WORSE") is None


def test_indicator_analysis_frame_exposes_evidence_and_relation() -> None:
    section = SimpleNamespace(
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
                "R002",
                0.05,
                0.00,
                "TRIGGERED",
                "LOWER_IS_WORSE",
                "EBITDA Margin",
            ),
            _rule(
                "R003",
                3.00,
                5.00,
                "NOT_TRIGGERED",
                "HIGHER_IS_WORSE",
                "NFP / EBITDA",
            ),
            _rule(
                "R004",
                None,
                2.00,
                "NOT_EVALUABLE",
                "LOWER_IS_WORSE",
                "Interest Coverage",
            ),
        ]
    )

    frame = build_indicator_analysis_frame(section)

    assert list(frame["Rule"]) == ["R001", "R002", "R003"]
    assert frame.loc[0, "Distance"] == pytest.approx(1.0)
    assert frame.loc[0, "Relation"] == "Worse than threshold"
    assert pd.isna(frame.loc[1, "Distance"])
    assert frame.loc[1, "Relation"] == "Threshold = 0"
    assert frame.loc[2, "Distance"] == pytest.approx(-0.4)
    assert frame.loc[2, "Relation"] == "Better than threshold"
