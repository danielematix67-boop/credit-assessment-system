from src.models.position import CreditPosition


def test_credit_position_creation():
    position = CreditPosition(
        position_id="POS001",
        revenue=1000000,
        revenue_growth=-0.15,
        change_in_finished_goods_inventory=20000,
        operating_grants=5000,
        net_purchases=400000,
        change_in_raw_materials_inventory=-10000,
        costs_for_services_and_third_party_assets=150000,
        personnel_costs=200000,
        operating_value_added=255000,
        gross_operating_margin=55000,
        depreciation_tangible_assets=20000,
        working_capital_impairments=5000,
        operating_provisions=3000,
        net_operating_margin=27000,
        other_income_expenses_balance=-2000,
        ebitda=250000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=10000,
    )

    assert position.position_id == "POS001"

    # Income statement - inputs
    assert position.revenue == 1000000
    assert position.change_in_finished_goods_inventory == 20000
    assert position.operating_grants == 5000
    assert position.net_purchases == 400000
    assert position.change_in_raw_materials_inventory == -10000
    assert position.costs_for_services_and_third_party_assets == 150000
    assert position.personnel_costs == 200000
    assert position.depreciation_tangible_assets == 20000
    assert position.working_capital_impairments == 5000
    assert position.operating_provisions == 3000
    assert position.other_income_expenses_balance == -2000

    # Income statement - derived
    assert position.operating_value_added == 255000
    assert position.gross_operating_margin == 55000
    assert position.net_operating_margin == 27000

    # Profitability
    assert position.ebitda == 250000
    assert position.profit_loss == -50000
    assert position.ebitda_margin == -0.05

    # Leverage / financial structure
    assert position.pfn_to_ebitda == 3.5
    assert position.interest_expense == 10000

    # Historical / variation data
    assert position.revenue_growth == -0.15


def test_credit_position_optional_fields_default_to_none():
    position = CreditPosition(
        position_id="POS002",
    )

    assert position.position_id == "POS002"

    assert position.revenue is None
    assert position.revenue_growth is None
    assert position.change_in_finished_goods_inventory is None
    assert position.operating_grants is None
    assert position.net_purchases is None
    assert position.change_in_raw_materials_inventory is None
    assert position.costs_for_services_and_third_party_assets is None
    assert position.personnel_costs is None
    assert position.operating_value_added is None
    assert position.gross_operating_margin is None
    assert position.depreciation_tangible_assets is None
    assert position.working_capital_impairments is None
    assert position.operating_provisions is None
    assert position.net_operating_margin is None
    assert position.other_income_expenses_balance is None
    assert position.ebitda is None
    assert position.profit_loss is None
    assert position.ebitda_margin is None
    assert position.pfn_to_ebitda is None
    assert position.interest_expense is None

