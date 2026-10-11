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
    production_value: float | None = None
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
    contribution_margin: float | None = None

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

    nfp_to_ebitda: float | None = None
    interest_expense: float | None = None

    # =========================
    # Historical / variation data
    # =========================

    revenue_growth: float | None = None

    # Bank debt levels for current year and four prior annual observations.
    bank_debt_current: float | None = None
    bank_debt_1y_ago: float | None = None
    bank_debt_2y_ago: float | None = None
    bank_debt_3y_ago: float | None = None
    bank_debt_4y_ago: float | None = None

    # Trade-payables levels for current year and four prior annual observations.
    trade_payables_current: float | None = None
    trade_payables_1y_ago: float | None = None
    trade_payables_2y_ago: float | None = None
    trade_payables_3y_ago: float | None = None
    trade_payables_4y_ago: float | None = None

    # Average payment days for the current year and four prior annual observations.
    avg_payment_days_current: float | None = None
    avg_payment_days_1y_ago: float | None = None
    avg_payment_days_2y_ago: float | None = None
    avg_payment_days_3y_ago: float | None = None
    avg_payment_days_4y_ago: float | None = None
