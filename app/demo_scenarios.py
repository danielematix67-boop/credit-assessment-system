from typing import Any


DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "Healthy Company": {
        "description": (
            "Stable financial profile with healthy profitability "
            "and moderate leverage."
        ),
        "data": {
            "position_id": "DEMO-001",
            "revenue_growth": 0.08,
            "ebitda": 5_000_000.0,
            "profit_loss": 2_500_000.0,
            "ebitda_margin": 0.18,
            "pfn_to_ebitda": 1.5,
        },
    },
    "Watchlist Company": {
        "description": (
            "Moderate deterioration in financial performance "
            "requiring closer monitoring."
        ),
        "data": {
            "position_id": "DEMO-002",
            "revenue_growth": -0.05,
            "ebitda": 3_000_000.0,
            "profit_loss": 800_000.0,
            "ebitda_margin": 0.08,
            "pfn_to_ebitda": 3.2,
        },
    },
    "High Risk Company": {
        "description": (
            "Significant deterioration in profitability and "
            "elevated financial leverage."
        ),
        "data": {
            "position_id": "DEMO-003",
            "revenue_growth": -0.15,
            "ebitda": 1_200_000.0,
            "profit_loss": -500_000.0,
            "ebitda_margin": 0.035,
            "pfn_to_ebitda": 5.8,
        },
    },
    "Missing Data Company": {
        "description": (
            "Financial information is incomplete, demonstrating "
            "how the system handles non-evaluable rules."
        ),
        "data": {
            "position_id": "DEMO-004",
            "revenue_growth": -0.03,
            "ebitda": None,
            "profit_loss": None,
            "ebitda_margin": None,
            "pfn_to_ebitda": None,
        },
    },
}


def get_demo_scenario_names() -> list[str]:
    """Return the names of all available demo scenarios."""

    return list(DEMO_SCENARIOS.keys())


def get_demo_scenario(
    scenario_name: str,
) -> dict[str, Any]:
    """
    Return the data associated with a demo scenario.
    """

    try:
        scenario = DEMO_SCENARIOS[scenario_name]

    except KeyError:
        raise ValueError(
            f"Unknown demo scenario: {scenario_name}"
        ) from None

    return scenario["data"].copy()


def get_demo_scenario_description(
    scenario_name: str,
) -> str:
    """
    Return the description associated with a demo scenario.
    """

    try:
        scenario = DEMO_SCENARIOS[scenario_name]

    except KeyError:
        raise ValueError(
            f"Unknown demo scenario: {scenario_name}"
        ) from None

    return str(scenario["description"])