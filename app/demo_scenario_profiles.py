from copy import deepcopy
from typing import Any


FOCUSED_SCENARIOS: dict[str, dict[str, Any]] = {
    "Customer Profile Stress": {
        "description": (
            "A controlled customer-profile stress case. Financial performance, "
            "banking behaviour and debt-service capacity remain sound, while "
            "all three customer-profile indicators are deliberately activated."
        ),
        "base": "Healthy Company",
        "overrides": {
            "values": {},
            "case_data": {
                "customer_profile": {
                    "active_ews": True,
                    "previous_restructuring": True,
                    "business_history_years": 1,
                }
            },
        },
    },
    "Financial Stress": {
        "description": (
            "A focused financial-analysis stress case. Customer profile, banking "
            "behaviour and debt sustainability remain broadly sound, while the "
            "financial rule engine identifies revenue, profitability, leverage and "
            "interest-coverage deterioration."
        ),
        "base": "Healthy Company",
        "overrides": {
            "values": {
                "revenue_growth": -0.35,
                "ebitda": -200_000.0,
                "ebitda_margin": -0.12,
                "nfp_to_ebitda": 8.0,
                "interest_expense": 300_000.0,
                "change_in_finished_goods_inventory": 500_000.0,
            },
            "case_data": {},
        },
    },
    "Behavioural Stress - Isolated": {
        "description": (
            "A focused behavioural-monitoring case. Financial performance, customer "
            "profile and debt-service capacity remain sound, while all four behavioural "
            "rules are deliberately activated."
        ),
        "base": "Healthy Company",
        "overrides": {
            "values": {},
            "case_data": {
                "behavioural": {
                    "average_utilization": 0.97,
                    "overdraft_days": 35,
                    "payment_delay_days": 65,
                    "exposure_growth": 0.45,
                }
            },
        },
    },
    "Debt Sustainability Stress": {
        "description": (
            "A focused debt-sustainability case. Customer profile, financial indicators "
            "and banking behaviour remain sound, while DSCR, debt-service burden and "
            "cash-flow headroom deteriorate simultaneously."
        ),
        "base": "Healthy Company",
        "overrides": {
            "values": {
                "ebitda": 500_000.0,
            },
            "case_data": {
                "debt_sustainability": {
                    "cash_flow_available_for_debt_service": 500_000.0,
                    "debt_service": 700_000.0,
                    "ebitda": 500_000.0,
                    "interest_expense": 150_000.0,
                }
            },
        },
    },
}


def extend_demo_scenarios(scenarios: dict[str, dict[str, Any]]) -> None:
    """Add focused, domain-isolated scenarios to the base demo catalogue."""
    for scenario_name, specification in FOCUSED_SCENARIOS.items():
        base_name = specification["base"]
        scenario = deepcopy(scenarios[base_name])
        scenario["description"] = specification["description"]
        scenario["values"].update(specification["overrides"].get("values", {}))

        for domain, overrides in specification["overrides"].get("case_data", {}).items():
            scenario["case_data"][domain].update(overrides)

        scenario["values"]["position_id"] = (
            f"DEMO-{scenario_name.upper().replace(' ', '-').replace(' - ', '-')}-001"
        )
        scenarios[scenario_name] = scenario
