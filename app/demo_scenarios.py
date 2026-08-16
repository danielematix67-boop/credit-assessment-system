from dataclasses import fields
from typing import Any

from src.models.position import CreditPosition


# ============================================================
# Demo Scenarios
# ============================================================

DEMO_SCENARIOS = {
    "Healthy Company": {
        "description": (
            "A financially solid company with positive revenue growth, "
            "positive profitability, healthy margins and moderate leverage."
        ),
        "values": {
            "position_id": "DEMO-HEALTHY-001",
            "revenue_growth": 0.08,
            "ebitda": 500_000.0,
            "profit_loss": 220_000.0,
            "ebitda_margin": 0.18,
            "pfn_to_ebitda": 1.5,
        },
    },
    "Revenue Deterioration": {
        "description": (
            "A company experiencing a significant contraction in revenues "
            "while maintaining otherwise relatively stable fundamentals."
        ),
        "values": {
            "position_id": "DEMO-REVENUE-001",
            "revenue_growth": -0.15,
            "ebitda": 350_000.0,
            "profit_loss": 120_000.0,
            "ebitda_margin": 0.12,
            "pfn_to_ebitda": 2.0,
        },
    },
    "Profitability Stress": {
        "description": (
            "A company showing deterioration in profitability and margins "
            "despite still generating positive EBITDA."
        ),
        "values": {
            "position_id": "DEMO-PROFITABILITY-001",
            "revenue_growth": 0.02,
            "ebitda": 150_000.0,
            "profit_loss": -50_000.0,
            "ebitda_margin": 0.025,
            "pfn_to_ebitda": 3.0,
        },
    },
    "Leverage Stress": {
        "description": (
            "A company with significant financial leverage. "
            "Operating performance remains positive, but debt capacity "
            "represents the main risk factor."
        ),
        "values": {
            "position_id": "DEMO-LEVERAGE-001",
            "revenue_growth": 0.03,
            "ebitda": 400_000.0,
            "profit_loss": 100_000.0,
            "ebitda_margin": 0.14,
            "pfn_to_ebitda": 6.0,
        },
    },
    "Multiple Risk Factors": {
        "description": (
            "A distressed company combining revenue contraction, "
            "negative EBITDA, negative profitability and high leverage."
        ),
        "values": {
            "position_id": "DEMO-MULTIPLE-RISK-001",
            "revenue_growth": -0.20,
            "ebitda": -120_000.0,
            "profit_loss": -180_000.0,
            "ebitda_margin": -0.08,
            "pfn_to_ebitda": 7.0,
        },
    },
    "Missing Information": {
        "description": (
            "A company for which several financial indicators are "
            "unavailable. This scenario demonstrates NOT_EVALUABLE "
            "handling and data-quality limitations."
        ),
        "values": {
            "position_id": "DEMO-MISSING-001",
            "revenue_growth": None,
            "ebitda": None,
            "profit_loss": None,
            "ebitda_margin": None,
            "pfn_to_ebitda": None,
        },
    },
}


# ============================================================
# Demo Position Builder
# ============================================================

def build_demo_position(
    scenario_name: str,
) -> CreditPosition:
    """
    Build a CreditPosition from a predefined demo scenario.

    Demo scenarios contain input data only.

    They do not contain:
    - rule outcomes
    - thresholds
    - severity decisions
    - assessment status
    - risk classifications

    All assessment logic remains inside the deterministic
    assessment workflow.
    """

    if scenario_name not in DEMO_SCENARIOS:
        raise ValueError(
            f"Unknown demo scenario: {scenario_name}"
        )

    scenario_values = DEMO_SCENARIOS[
        scenario_name
    ]["values"]

    position_data: dict[str, Any] = {}

    for field in fields(CreditPosition):

        field_name = field.name

        if field_name in scenario_values:

            position_data[field_name] = (
                scenario_values[field_name]
            )

            continue

        # If a field is added to CreditPosition in the future,
        # fail explicitly rather than silently inventing financial data.
        raise ValueError(
            f"Demo scenario '{scenario_name}' does not define "
            f"the required CreditPosition field '{field_name}'. "
            "Update demo_scenarios.py."
        )

    return CreditPosition(
        **position_data
    )