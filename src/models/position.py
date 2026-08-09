from dataclasses import dataclass

# CreditPosition represents the input data used by the assessment engine.
#
# It should contain business and financial data, but no rule-evaluation logic.
#
# Rules read the position and independently determine whether their conditions
# are triggered. Missing financial information is represented by None.

@dataclass
class CreditPosition:
    position_id: str

    # =========================
    # Income statement - inputs
    # =========================

    revenue: float | None = None
    change_in_finished_goods_inventory: float | None = None
    operating_grants: float | None = None
    net_purchases: float | None = None
    change_in_raw_materials_inventory: float | None = None
    costs_for_services_and_third_party_assets: float | None = None
    personnel_costs: float | None = None
    depreciation_tangible_assets: float | None = None
    working_capital_impairments: float | None = None
    operating_provisions: float | None = None
    other_income_expenses_balance: float | None = None

    # =========================
    # Income statement - derived
    # =========================

    operating_value_added: float | None = None
    gross_operating_margin: float | None = None
    net_operating_margin: float | None = None

    # =========================
    # Profitability
    # =========================

    ebitda: float | None = None
    profit_loss: float | None = None
    ebitda_margin: float | None = None
    ebitda_inventory_contribution: float | None = None

    # =========================
    # Leverage / financial structure
    # =========================

    pfn_to_ebitda: float | None = None
    interest_expense: float | None = None

    # =========================
    # Historical / variation data
    # =========================

    revenue_growth: float | None = None

    