"""Backward-compatible exports for the CreditPosition input UI.

The implementation now lives in ``app.ui.input``. This module is retained so
existing imports continue to work without coupling callers to the package
structure.
"""

from app.ui.input.credit_position import (
    build_credit_position_from_ui,
    build_manual_case_data_from_ui,
    create_optional_numeric_field,
    create_streamlit_field,
    display_position_table,
)
from app.ui.input.field_metadata import (
    FIELD_GROUPS,
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
