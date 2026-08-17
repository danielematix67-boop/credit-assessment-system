import pytest

from src.models.position import CreditPosition


@pytest.fixture
def position_data():
    return {
        "position_id": "TEST_POSITION",
        "revenue": 1_000_000,
        "revenue_growth": -0.15,
        "change_in_finished_goods_inventory": 20_000,
        "operating_grants": 5_000,
        "net_purchases": 400_000,
        "change_in_raw_materials_inventory": -10_000,
        "costs_for_services_and_third_party_assets": 150_000,
        "personnel_costs": 200_000,
        "operating_value_added": 255_000,
        "gross_operating_margin": 55_000,
        "depreciation_tangible_assets": 20_000,
        "working_capital_impairments": 5_000,
        "operating_provisions": 3_000,
        "net_operating_margin": 27_000,
        "other_income_expenses_balance": -2_000,
        "ebitda": 250_000,
        "profit_loss": -50_000,
        "ebitda_margin": -0.05,
        "nfp_to_ebitda": 3.5,
        "interest_expense": 10_000,
    }


@pytest.fixture
def credit_position(position_data):
    return CreditPosition(**position_data)


def test_credit_position_preserves_provided_data(
    credit_position,
    position_data,
):
    for field_name, expected_value in position_data.items():
        assert getattr(credit_position, field_name) == expected_value


def test_credit_position_preserves_position_identifier(
    credit_position,
    position_data,
):
    assert (
        credit_position.position_id
        == position_data["position_id"]
    )


def test_credit_position_optional_fields_default_to_none():
    position = CreditPosition(
        position_id="TEST_POSITION",
    )

    optional_fields = (
        "revenue",
        "revenue_growth",
        "change_in_finished_goods_inventory",
        "operating_grants",
        "net_purchases",
        "change_in_raw_materials_inventory",
        "costs_for_services_and_third_party_assets",
        "personnel_costs",
        "operating_value_added",
        "gross_operating_margin",
        "depreciation_tangible_assets",
        "working_capital_impairments",
        "operating_provisions",
        "net_operating_margin",
        "other_income_expenses_balance",
        "ebitda",
        "profit_loss",
        "ebitda_margin",
        "nfp_to_ebitda",
        "interest_expense",
    )

    for field_name in optional_fields:
        assert getattr(position, field_name) is None