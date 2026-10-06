from copy import deepcopy
from dataclasses import fields
from typing import Any

from src.models.behavioural_data import BehaviouralData
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.ews_score import EwsScoreClass
from src.models.position import CreditPosition

# The demo catalog intentionally contains one complete credit case. It populates
# every assessment domain so the Results page can expose the full deterministic
# rule inventory in a single end-to-end scenario.
_BASE_VALUES: dict[str, Any] = {
    "position_id": "DEMO-INTEGRATED-001",
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
    "operating_value_added": 3_500_000.0,
    "gross_operating_margin": 1_500_000.0,
    "net_operating_margin": 1_200_000.0,
    "ebitda": -200_000.0,
    "profit_loss": -350_000.0,
    "ebitda_margin": -0.10,
    "ebitda_inventory_contribution": 0.01,
    "nfp_to_ebitda": None,
    "interest_expense": 700_000.0,
    "revenue_growth": -0.35,
}

_BASE_CASE_DATA: dict[str, dict[str, Any]] = {
    "customer_profile": {
        "company_name": "Epsilon Industrial S.p.A.",
        "counterparty_type": "Company",
        "legal_form": "S.p.A.",
        "sector": "Industrial manufacturing",
        "size_class": "Mid-cap",
        "geography": "Northern Italy",
        "business_history_years": 1,
        "operations": ["Industrial manufacturing", "B2B equipment supply"],
        "forborne_non_performing_exit": False,
        "past_due_count": 4,
        "cure_period_days": 0,
        "monitoring_period_days": 90,
        "probation_period_days": 180,
        "minimum_regulatory_risk_grade": "Past Due",
        "previous_risk_grade": "Bonis",
        "risk_grade_change": "Bonis → Past Due",
        "ews_score_class": EwsScoreClass.LIGHT_RED,
        "ews_score_notching": "Downward notching",
        "ews_score_variation": -0.18,
        "active_ewis": [
            "Revenue deterioration",
            "High credit utilization",
            "Payment delay",
        ],
        "rating": "BB-",
        "rating_notching": "Downward notching due to financial deterioration",
        "rating_influential_factors": ["Leverage", "Liquidity", "Profitability"],
        "rating_elementary_modules": ["Financial profile", "Behavioural profile"],
        "pd": 0.082,
        "risk_group_interdependence": "Moderate",
        "risk_group_independence": "Low",
        "shareholders": ["Family holding", "Management shareholders"],
        "shareholder_roles": ["Controlling shareholder", "Executive shareholder"],
        "management_members": ["CEO", "CFO"],
        "generational_transition": False,
        "employment_contract_type": None,
        "economic_family_context": None,
        "relationship_years": 2,
        "historical_facilities": ["Revolving credit", "Term loan"],
        "previous_restructuring": True,
        "forborne": True,
        "protests": [],
        "bankruptcies": [],
        "litigation": ["Commercial dispute - ongoing"],
        "significant_historical_events": ["Ownership restructuring in 2024"],
    },
    "behavioural": {
        "average_utilization": 0.97,
        "overdraft_days": 45,
        "payment_delay_days": 75,
        "exposure_growth": 0.48,
    },
    "debt_sustainability": {
        "cash_flow_available_for_debt_service": 100_000.0,
        "debt_service": 600_000.0,
        "ebitda": 500_000.0,
        "interest_expense": 700_000.0,
    },
}


def _scenario(
    name: str,
    description: str,
    *,
    values: dict[str, Any] | None = None,
    case_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged_values = deepcopy(_BASE_VALUES)
    merged_case_data = deepcopy(_BASE_CASE_DATA)
    merged_values.update(values or {})
    for domain, domain_values in (case_data or {}).items():
        merged_case_data[domain].update(domain_values)
    merged_values["position_id"] = name.split(" · ", maxsplit=1)[0].replace(" ", "-")
    return {
        "description": description,
        "values": merged_values,
        "case_data": merged_case_data,
    }


DEMO_SCENARIOS = {
    "01 · Complete Credit Assessment": _scenario(
        "01 · Complete Credit Assessment",
        (
            "Single end-to-end synthetic credit case covering every configured "
            "assessment domain and exposing the complete deterministic rule evidence "
            "for customer profile, financial analysis, behavioural analysis and debt sustainability."
        ),
    ),
}


def build_demo_position(scenario_name: str) -> CreditPosition:
    """Build a CreditPosition from the predefined scenario catalog."""
    if scenario_name not in DEMO_SCENARIOS:
        raise ValueError(f"Unknown demo scenario: {scenario_name}")

    scenario_values = DEMO_SCENARIOS[scenario_name]["values"]
    position_data: dict[str, Any] = {}
    for field in fields(CreditPosition):
        if field.name not in scenario_values:
            raise ValueError(
                f"Scenario '{scenario_name}' does not define required field '{field.name}'."
            )
        position_data[field.name] = scenario_values[field.name]
    return CreditPosition(**position_data)


def build_demo_case_data(
    scenario_name: str,
) -> tuple[
    CustomerProfileData | None,
    BehaviouralData | None,
    DebtSustainabilityData | None,
]:
    """Build synthetic case-level inputs for a predefined scenario."""
    if scenario_name not in DEMO_SCENARIOS:
        raise ValueError(f"Unknown demo scenario: {scenario_name}")

    case_data = DEMO_SCENARIOS[scenario_name].get("case_data", {})
    if not case_data:
        return None, None, None

    return (
        CustomerProfileData(**case_data["customer_profile"]),
        BehaviouralData(**case_data["behavioural"]),
        DebtSustainabilityData(**case_data["debt_sustainability"]),
    )
