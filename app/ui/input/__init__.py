"""Credit position input UI and presentation metadata."""

from app.ui.input.credit_position import (
    build_credit_position_from_ui,
    build_manual_case_data_from_ui,
    create_optional_numeric_field,
    create_streamlit_field,
    display_position_table,
)
from app.ui.input.field_metadata import (
    FIELD_GROUPS,
    build_scenario_data_table,
    format_field_description,
    format_field_label,
    format_field_value,
    get_credit_position_fields,
    get_credit_position_type_hints,
    get_field_default,
    get_field_unit,
    unwrap_optional,
)

__all__ = [
    "FIELD_GROUPS",
    "build_credit_position_from_ui",
    "build_manual_case_data_from_ui",
    "build_scenario_data_table",
    "create_optional_numeric_field",
    "create_streamlit_field",
    "display_position_table",
    "format_field_description",
    "format_field_label",
    "format_field_value",
    "get_credit_position_fields",
    "get_credit_position_type_hints",
    "get_field_default",
    "get_field_unit",
    "unwrap_optional",
]
