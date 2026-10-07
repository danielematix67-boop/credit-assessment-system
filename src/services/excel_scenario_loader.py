from dataclasses import fields
from io import BytesIO
from typing import Any, BinaryIO

import pandas as pd  # type: ignore[import-untyped]

from src.models.behavioural_data import BehaviouralData
from src.models.customer_profile_data import REGULATORY_RISK_GRADES, CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.ews_score import EwsScoreClass
from src.models.position import CreditPosition

SHEET_MODELS = {
    "Financial Analysis": CreditPosition,
    "Customer Profile": CustomerProfileData,
    "Behavioural Analysis": BehaviouralData,
    "Debt Sustainability": DebtSustainabilityData,
}

LIST_FIELDS = {
    "operations",
    "active_ewis",
    "rating_influential_factors",
    "rating_elementary_modules",
    "shareholders",
    "shareholder_roles",
    "management_members",
    "historical_facilities",
    "protests",
    "bankruptcies",
    "litigation",
    "significant_historical_events",
}

BOOL_FIELDS = {
    "forborne_non_performing_exit",
    "generational_transition",
    "previous_restructuring",
    "forborne",
}

INT_FIELDS = {
    "business_history_years",
    "past_due_count",
    "cure_period_days",
    "monitoring_period_days",
    "probation_period_days",
    "relationship_years",
}

FLOAT_FIELDS = {
    field.name
    for model in (CreditPosition, BehaviouralData, DebtSustainabilityData)
    for field in fields(model)
    if field.name != "position_id"
} | {
    "ews_score_variation",
    "pd",
}


class ExcelScenarioError(ValueError):
    """Raised when an uploaded Excel workbook does not match the input contract."""


def load_excel_scenarios(file: BinaryIO | bytes) -> dict[str, tuple[
    CreditPosition,
    CustomerProfileData | None,
    BehaviouralData | None,
    DebtSustainabilityData | None,
]]:
    """Load and validate one or more assessment scenarios from an Excel workbook."""

    if isinstance(file, bytes):
        file = BytesIO(file)

    try:
        workbook = pd.ExcelFile(file, engine="openpyxl")
    except Exception as error:
        raise ExcelScenarioError(
            "Unable to read the Excel workbook. Please upload a valid .xlsx file."
        ) from error

    missing = {"Financial Analysis"} - set(workbook.sheet_names)
    if missing:
        raise ExcelScenarioError(
            "Missing required sheet(s): " + ", ".join(sorted(missing)) + "."
        )

    frames: dict[str, pd.DataFrame] = {}
    for sheet_name, model in SHEET_MODELS.items():
        if sheet_name not in workbook.sheet_names:
            continue
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        frames[sheet_name] = _validate_frame(sheet_name, frame, model)

    scenario_ids = frames["Financial Analysis"]["scenario_id"].tolist()
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ExcelScenarioError(
            "Sheet 'Financial Analysis' contains duplicate scenario_id values."
        )

    for sheet_name, frame in frames.items():
        ids = set(frame["scenario_id"])
        unknown = ids - set(scenario_ids)
        if unknown:
            raise ExcelScenarioError(
                f"Sheet '{sheet_name}' contains unknown scenario_id values: "
                + ", ".join(sorted(map(str, unknown)))
                + "."
            )

    result = {}
    for scenario_id in scenario_ids:
        position = _build_model(
            CreditPosition,
            frames["Financial Analysis"],
            scenario_id,
            inject_position_id=True,
        )
        customer_profile = (
            _build_model(CustomerProfileData, frames["Customer Profile"], scenario_id)
            if "Customer Profile" in frames
            else None
        )
        behavioural = (
            _build_model(BehaviouralData, frames["Behavioural Analysis"], scenario_id)
            if "Behavioural Analysis" in frames
            else None
        )
        debt_sustainability = (
            _build_model(
                DebtSustainabilityData,
                frames["Debt Sustainability"],
                scenario_id,
            )
            if "Debt Sustainability" in frames
            else None
        )
        result[scenario_id] = (
            position,
            customer_profile,
            behavioural,
            debt_sustainability,
        )

    return result


def _validate_frame(
    sheet_name: str,
    frame: pd.DataFrame,
    model: type[Any],
) -> pd.DataFrame:
    if "scenario_id" not in frame.columns:
        raise ExcelScenarioError(
            f"Sheet '{sheet_name}' must contain a 'scenario_id' column."
        )

    if frame.empty:
        raise ExcelScenarioError(f"Sheet '{sheet_name}' is empty.")

    allowed = {"scenario_id"} | {
        field.name
        for field in fields(model)
        if not (sheet_name == "Financial Analysis" and field.name == "position_id")
    }
    unknown = set(frame.columns) - allowed
    if unknown:
        raise ExcelScenarioError(
            f"Sheet '{sheet_name}' contains unsupported column(s): "
            + ", ".join(sorted(map(str, unknown)))
            + "."
        )

    normalized = frame.copy()
    normalized["scenario_id"] = normalized["scenario_id"].map(_scenario_id)
    if normalized["scenario_id"].eq("").any():
        raise ExcelScenarioError(
            f"Sheet '{sheet_name}' contains a blank scenario_id."
        )
    return normalized


def _build_model(
    model: type[Any],
    frame: pd.DataFrame,
    scenario_id: str,
    *,
    inject_position_id: bool = False,
) -> Any:
    matches = frame.loc[frame["scenario_id"] == scenario_id]
    if matches.empty:
        return None
    if len(matches) > 1:
        raise ExcelScenarioError(
            f"Sheet contains multiple rows for scenario_id '{scenario_id}'."
        )

    row = matches.iloc[0].to_dict()
    values: dict[str, Any] = {}
    for field in fields(model):
        if field.name == "position_id" and inject_position_id:
            values[field.name] = scenario_id
            continue
        if field.name not in row:
            values[field.name] = None if field.name not in LIST_FIELDS else []
            continue
        values[field.name] = _convert_value(field.name, row[field.name])

    if model is CustomerProfileData:
        _validate_customer_profile(values, scenario_id)

    return model(**values)


def _convert_value(field_name: str, value: Any) -> Any:
    if pd.isna(value):
        return [] if field_name in LIST_FIELDS else None

    if field_name in LIST_FIELDS:
        return [item.strip() for item in str(value).split(";") if item.strip()]

    if field_name in BOOL_FIELDS:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "yes", "y", "1"}:
            return True
        if normalized in {"false", "no", "n", "0"}:
            return False
        raise ExcelScenarioError(
            f"Invalid boolean value for '{field_name}': {value!r}. "
            "Use TRUE/FALSE or Yes/No."
        )

    if field_name in INT_FIELDS:
        try:
            numeric = float(value)
            if not numeric.is_integer():
                raise ValueError
            return int(numeric)
        except (TypeError, ValueError) as error:
            raise ExcelScenarioError(
                f"Invalid integer value for '{field_name}': {value!r}."
            ) from error

    if field_name in FLOAT_FIELDS:
        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise ExcelScenarioError(
                f"Invalid numeric value for '{field_name}': {value!r}."
            ) from error

    if field_name == "ews_score_class":
        try:
            return EwsScoreClass(str(value).strip().upper())
        except ValueError as error:
            allowed = ", ".join(item.value for item in EwsScoreClass)
            raise ExcelScenarioError(
                f"Invalid ews_score_class '{value}'. Allowed values: {allowed}."
            ) from error

    if field_name in {"minimum_regulatory_risk_grade", "previous_risk_grade"}:
        normalized = str(value).strip()
        if normalized not in REGULATORY_RISK_GRADES:
            raise ExcelScenarioError(
                f"Invalid {field_name} '{value}'. Allowed values: "
                + ", ".join(REGULATORY_RISK_GRADES)
                + "."
            )
        return normalized

    if field_name == "scenario_id":
        return _scenario_id(value)

    return str(value).strip()


def _validate_customer_profile(values: dict[str, Any], scenario_id: str) -> None:
    risk_change = values.get("risk_grade_change")
    if risk_change is not None and not str(risk_change).strip():
        values["risk_grade_change"] = None

    for field_name in ("minimum_regulatory_risk_grade", "previous_risk_grade"):
        value = values.get(field_name)
        if value is not None and value not in REGULATORY_RISK_GRADES:
            raise ExcelScenarioError(
                f"Scenario '{scenario_id}' has invalid {field_name}: {value!r}."
            )


def _scenario_id(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
