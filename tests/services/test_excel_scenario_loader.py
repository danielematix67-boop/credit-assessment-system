from io import BytesIO

import openpyxl
import pytest

from src.services.excel_scenario_loader import ExcelScenarioError, load_excel_scenarios


def _workbook_bytes(
    *,
    include_customer_profile: bool = True,
    minimum_regulatory_risk_grade: str = "Past Due",
) -> bytes:
    workbook = openpyxl.Workbook()
    credit = workbook.active
    credit.title = "Credit_Position"
    credit.append(["scenario_id", "revenue", "ebitda", "revenue_growth"])
    credit.append(["TEST-001", 1000000, 100000, 0.05])

    if include_customer_profile:
        profile = workbook.create_sheet("Customer_Profile")
        profile.append(
            [
                "scenario_id",
                "company_name",
                "minimum_regulatory_risk_grade",
                "ews_score_class",
                "active_ewis",
            ]
        )
        profile.append(
            [
                "TEST-001",
                "Test Company",
                minimum_regulatory_risk_grade,
                "YELLOW",
                "Revenue deterioration;Payment delay",
            ]
        )

    behavioural = workbook.create_sheet("Behavioural")
    behavioural.append(["scenario_id", "average_utilization"])
    behavioural.append(["TEST-001", 0.75])

    debt = workbook.create_sheet("Debt_Sustainability")
    debt.append(["scenario_id", "debt_service", "cash_flow_available_for_debt_service"])
    debt.append(["TEST-001", 200000, 300000])

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_load_excel_scenario_maps_to_domain_models() -> None:
    scenarios = load_excel_scenarios(_workbook_bytes())

    position, profile, behavioural, debt = scenarios["TEST-001"]

    assert position.position_id == "TEST-001"
    assert position.revenue == 1000000.0
    assert profile is not None
    assert profile.minimum_regulatory_risk_grade == "Past Due"
    assert profile.active_ewis == ["Revenue deterioration", "Payment delay"]
    assert behavioural is not None
    assert behavioural.average_utilization == 0.75
    assert debt is not None
    assert debt.debt_service == 200000.0


def test_optional_domain_sheet_can_be_omitted() -> None:
    scenarios = load_excel_scenarios(
        _workbook_bytes(include_customer_profile=False)
    )

    assert scenarios["TEST-001"][1] is None


def test_invalid_regulatory_risk_grade_is_rejected() -> None:
    with pytest.raises(ExcelScenarioError, match="Allowed values"):
        load_excel_scenarios(
            _workbook_bytes(minimum_regulatory_risk_grade="Substandard")
        )


def test_required_credit_position_sheet_is_rejected_when_missing() -> None:
    workbook = openpyxl.Workbook()
    workbook.active.title = "Customer_Profile"
    buffer = BytesIO()
    workbook.save(buffer)

    with pytest.raises(ExcelScenarioError, match="Credit_Position"):
        load_excel_scenarios(buffer.getvalue())
