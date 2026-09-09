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
            "strong operating performance, positive profitability, "
            "healthy margins and moderate leverage."
        ),
        "values": {
            "position_id": "DEMO-HEALTHY-001",
            # Income statement
            "revenue": 10_000_000.0,
            "change_in_finished_goods_inventory": 100_000.0,
            "operating_grants": 50_000.0,
            "net_purchases": 5_000_000.0,
            "change_in_raw_materials_inventory": -50_000.0,
            "costs_for_services_and_third_party_assets": 1_500_000.0,
            "personnel_costs": 2_000_000.0,
            "depreciation_tangible_assets": 300_000.0,
            "working_capital_impairments": 50_000.0,
            "operating_provisions": 30_000.0,
            "other_income_expenses_balance": 20_000.0,
            # Derived / operating indicators
            "operating_value_added": 3_500_000.0,
            "gross_operating_margin": 1_500_000.0,
            "net_operating_margin": 1_200_000.0,
            # Profitability
            "ebitda": 1_800_000.0,
            "profit_loss": 900_000.0,
            "ebitda_margin": 0.18,
            "ebitda_inventory_contribution": 0.01,
            # Leverage / financial structure
            "nfp_to_ebitda": 1.5,
            "interest_expense": 150_000.0,
            # Historical / variation data
            "revenue_growth": 0.08,
        },
    },
    "Revenue Deterioration": {
        "description": (
            "A company experiencing a significant contraction in revenues "
            "while maintaining positive profitability and relatively "
            "stable financial structure."
        ),
        "values": {
            "position_id": "DEMO-REVENUE-001",
            # Income statement
            "revenue": 8_500_000.0,
            "change_in_finished_goods_inventory": 80_000.0,
            "operating_grants": 40_000.0,
            "net_purchases": 4_300_000.0,
            "change_in_raw_materials_inventory": -40_000.0,
            "costs_for_services_and_third_party_assets": 1_300_000.0,
            "personnel_costs": 1_700_000.0,
            "depreciation_tangible_assets": 280_000.0,
            "working_capital_impairments": 40_000.0,
            "operating_provisions": 25_000.0,
            "other_income_expenses_balance": 10_000.0,
            # Derived / operating indicators
            "operating_value_added": 3_000_000.0,
            "gross_operating_margin": 1_200_000.0,
            "net_operating_margin": 900_000.0,
            # Profitability
            "ebitda": 1_020_000.0,
            "profit_loss": 420_000.0,
            "ebitda_margin": 0.12,
            "ebitda_inventory_contribution": 0.01,
            # Leverage / financial structure
            "nfp_to_ebitda": 2.0,
            "interest_expense": 180_000.0,
            # Historical / variation data
            "revenue_growth": -0.15,
        },
    },
    "Profitability Stress": {
        "description": (
            "A company showing deterioration in profitability and margins "
            "despite maintaining positive EBITDA and moderate revenue growth."
        ),
        "values": {
            "position_id": "DEMO-PROFITABILITY-001",
            # Income statement
            "revenue": 6_000_000.0,
            "change_in_finished_goods_inventory": 20_000.0,
            "operating_grants": 20_000.0,
            "net_purchases": 3_200_000.0,
            "change_in_raw_materials_inventory": -20_000.0,
            "costs_for_services_and_third_party_assets": 900_000.0,
            "personnel_costs": 1_400_000.0,
            "depreciation_tangible_assets": 180_000.0,
            "working_capital_impairments": 60_000.0,
            "operating_provisions": 40_000.0,
            "other_income_expenses_balance": -20_000.0,
            # Derived / operating indicators
            "operating_value_added": 1_900_000.0,
            "gross_operating_margin": 300_000.0,
            "net_operating_margin": 120_000.0,
            # Profitability
            "ebitda": 150_000.0,
            "profit_loss": -50_000.0,
            "ebitda_margin": 0.025,
            "ebitda_inventory_contribution": 0.005,
            # Leverage / financial structure
            "nfp_to_ebitda": 3.0,
            "interest_expense": 220_000.0,
            # Historical / variation data
            "revenue_growth": 0.02,
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
            # Income statement
            "revenue": 9_000_000.0,
            "change_in_finished_goods_inventory": 80_000.0,
            "operating_grants": 30_000.0,
            "net_purchases": 4_600_000.0,
            "change_in_raw_materials_inventory": -30_000.0,
            "costs_for_services_and_third_party_assets": 1_300_000.0,
            "personnel_costs": 1_800_000.0,
            "depreciation_tangible_assets": 300_000.0,
            "working_capital_impairments": 40_000.0,
            "operating_provisions": 30_000.0,
            "other_income_expenses_balance": 10_000.0,
            # Derived / operating indicators
            "operating_value_added": 3_200_000.0,
            "gross_operating_margin": 1_300_000.0,
            "net_operating_margin": 1_000_000.0,
            # Profitability
            "ebitda": 1_260_000.0,
            "profit_loss": 600_000.0,
            "ebitda_margin": 0.14,
            "ebitda_inventory_contribution": 0.01,
            # Leverage / financial structure
            "nfp_to_ebitda": 6.0,
            "interest_expense": 500_000.0,
            # Historical / variation data
            "revenue_growth": 0.03,
        },
    },
    "Multiple Risk Factors": {
        "description": (
            "A distressed company combining revenue contraction, "
            "negative EBITDA, negative profitability and high leverage."
        ),
        "values": {
            "position_id": "DEMO-MULTIPLE-RISK-001",
            # Income statement
            "revenue": 5_000_000.0,
            "change_in_finished_goods_inventory": -100_000.0,
            "operating_grants": 10_000.0,
            "net_purchases": 3_000_000.0,
            "change_in_raw_materials_inventory": 50_000.0,
            "costs_for_services_and_third_party_assets": 1_000_000.0,
            "personnel_costs": 1_300_000.0,
            "depreciation_tangible_assets": 250_000.0,
            "working_capital_impairments": 100_000.0,
            "operating_provisions": 80_000.0,
            "other_income_expenses_balance": -50_000.0,
            # Derived / operating indicators
            "operating_value_added": 900_000.0,
            "gross_operating_margin": -200_000.0,
            "net_operating_margin": -500_000.0,
            # Profitability
            "ebitda": -120_000.0,
            "profit_loss": -180_000.0,
            "ebitda_margin": -0.08,
            "ebitda_inventory_contribution": -0.02,
            # Leverage / financial structure
            "nfp_to_ebitda": 7.0,
            "interest_expense": 700_000.0,
            # Historical / variation data
            "revenue_growth": -0.20,
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
            # Income statement
            "revenue": None,
            "change_in_finished_goods_inventory": None,
            "operating_grants": None,
            "net_purchases": None,
            "change_in_raw_materials_inventory": None,
            "costs_for_services_and_third_party_assets": None,
            "personnel_costs": None,
            "depreciation_tangible_assets": None,
            "working_capital_impairments": None,
            "operating_provisions": None,
            "other_income_expenses_balance": None,
            # Derived / operating indicators
            "operating_value_added": None,
            "gross_operating_margin": None,
            "net_operating_margin": None,
            # Profitability
            "ebitda": None,
            "profit_loss": None,
            "ebitda_margin": None,
            "ebitda_inventory_contribution": None,
            # Leverage / financial structure
            "nfp_to_ebitda": None,
            "interest_expense": None,
            # Historical / variation data
            "revenue_growth": None,
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
        raise ValueError(f"Unknown demo scenario: {scenario_name}")

    scenario_values = DEMO_SCENARIOS[scenario_name]["values"]

    position_data: dict[str, Any] = {}

    for field in fields(CreditPosition):
        field_name = field.name

        if field_name in scenario_values:
            position_data[field_name] = scenario_values[field_name]
            continue

        raise ValueError(
            f"Demo scenario '{scenario_name}' does not define "
            f"the required CreditPosition field '{field_name}'. "
            "Update demo_scenarios.py."
        )

    return CreditPosition(**position_data)
