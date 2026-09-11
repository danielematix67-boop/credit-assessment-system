from copy import deepcopy
from dataclasses import fields
from typing import Any

from src.models.behavioural_data import BehaviouralData
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition


# Every scenario contains complete inputs for the four assessment domains.
# Synthetic values are deliberately chosen to activate the intended rules while
# keeping the remaining domains in a stable state. The deterministic Rule Engine
# remains the only source of assessment decisions.
_BASE_VALUES: dict[str, Any] = {
    "position_id": "DEMO-BASE-001",
    "revenue": 10_000_000.0,
    "change_in_finished_goods_inventory": 7_000_000.0,
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
    "ebitda": 1_800_000.0,
    "profit_loss": 900_000.0,
    "ebitda_margin": 0.18,
    "ebitda_inventory_contribution": 0.01,
    "nfp_to_ebitda": 1.5,
    "interest_expense": 150_000.0,
    "revenue_growth": 0.08,
}

_BASE_CASE_DATA: dict[str, dict[str, Any]] = {
    "customer_profile": {
        "company_name": "Alpina Manufacturing S.p.A.",
        "legal_form": "S.p.A.",
        "sector": "Industrial manufacturing",
        "size_class": "Mid-cap",
        "geography": "Northern Italy",
        "shareholders": ["Family holding", "Management shareholders"],
        "management_members": ["CEO", "CFO"],
        "relationship_years": 8,
        "business_history_years": 24,
        "historical_facilities": ["Revolving credit", "Term loan"],
        "active_ews": False,
        "previous_restructuring": False,
    },
    "behavioural": {
        "average_utilization": 0.42,
        "overdraft_days": 1,
        "payment_delay_days": 2,
        "exposure_growth": 0.04,
    },
    "debt_sustainability": {
        "cash_flow_available_for_debt_service": 1_200_000.0,
        "debt_service": 450_000.0,
        "ebitda": 1_800_000.0,
        "interest_expense": 150_000.0,
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
    "01 · Baseline": _scenario(
        "01 · Baseline",
        "Complete low-risk borrower profile. All four assessment domains are populated and no configured rule is intentionally triggered.",
    ),
    "02 · Customer Profile Risk": _scenario(
        "02 · Customer Profile Risk",
        "Focused customer-profile case activating CP001, CP002 and CP003 while financial, behavioural and debt-sustainability inputs remain stable.",
        case_data={
            "customer_profile": {
                "company_name": "Beta Early Stage S.r.l.",
                "active_ews": True,
                "previous_restructuring": True,
                "business_history_years": 1,
            }
        },
    ),
    "03 · Revenue & Profitability Risk": _scenario(
        "03 · Revenue & Profitability Risk",
        (
            "Focused financial-analysis case activating R001, R002 and R003: "
            "revenue contraction, negative EBITDA and negative EBITDA margin."
        ),
        values={
            "revenue": 6_000_000.0,
            "change_in_finished_goods_inventory": 100_000.0,
            "ebitda": -200_000.0,
            "profit_loss": -300_000.0,
            "ebitda_margin": -0.12,
            "revenue_growth": -0.35,
            "nfp_to_ebitda": None,
            "interest_expense": 150_000.0,
        },
    ),
    "04 · Leverage & Interest Risk": _scenario(
        "04 · Leverage & Interest Risk",
        (
            "Focused financial-analysis case activating R004, R005 and R007 "
            "through excessive leverage, high interest burden and weak interest coverage."
        ),
        values={
            "nfp_to_ebitda": 8.0,
            "interest_expense": 1_200_000.0,
            "ebitda": 1_000_000.0,
            "ebitda_margin": 0.10,
        },
    ),
    "05 · Profitability Quality Risk": _scenario(
        "05 · Profitability Quality Risk",
        (
            "Focused financial-quality case activating R006: EBITDA is materially "
            "supported by the increase in finished-goods inventory."
        ),
        values={
            "ebitda": 1_800_000.0,
            "change_in_finished_goods_inventory": 100_000.0,
        },
    ),
    "06 · Behavioural Risk": _scenario(
        "06 · Behavioural Risk",
        (
            "Focused behavioural-monitoring case activating B001, B002, B003 and "
            "B004 through high utilization, prolonged overdraft, payment delays and exposure growth."
        ),
        case_data={
            "customer_profile": {"company_name": "Futura Logistics S.p.A."},
            "behavioural": {
                "average_utilization": 0.97,
                "overdraft_days": 35,
                "payment_delay_days": 65,
                "exposure_growth": 0.45,
            },
        },
    ),
    "07 · Debt Sustainability Risk": _scenario(
        "07 · Debt Sustainability Risk",
        (
            "Focused debt-sustainability case activating DS001, DS002 and DS003 "
            "through insufficient DSCR, excessive debt service relative to EBITDA and a negative cash-flow buffer."
        ),
        values={"ebitda": 500_000.0},
        case_data={
            "debt_sustainability": {
                "cash_flow_available_for_debt_service": 500_000.0,
                "debt_service": 700_000.0,
                "ebitda": 500_000.0,
                "interest_expense": 150_000.0,
            }
        },
    ),
    "08 · Integrated Credit Stress": _scenario(
        "08 · Integrated Credit Stress",
        (
            "End-to-end stressed borrower combining customer-profile, financial, behavioural and "
            "debt-sustainability deterioration. This is the main cumulative-risk demonstration."
        ),
        values={
            "change_in_finished_goods_inventory": 100_000.0,
            "ebitda": -200_000.0,
            "profit_loss": -350_000.0,
            "ebitda_margin": -0.10,
            "nfp_to_ebitda": None,
            "interest_expense": 700_000.0,
            "revenue_growth": -0.35,
        },
        case_data={
            "customer_profile": {
                "company_name": "Epsilon Industrial S.p.A.",
                "active_ews": True,
                "previous_restructuring": True,
                "business_history_years": 1,
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
                "ebitda": -200_000.0,
                "interest_expense": 700_000.0,
            },
        },
    ),
    "09 · Data Availability": {
        "description": (
            "Data-quality scenario with financial and domain-level inputs unavailable. "
            "The assessment must preserve NOT_EVALUABLE evidence and expose limitations "
            "rather than infer missing values."
        ),
        "values": {field.name: None for field in fields(CreditPosition)},
        "case_data": {},
    },
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
