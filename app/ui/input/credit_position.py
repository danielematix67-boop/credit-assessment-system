"""Streamlit rendering for CreditPosition input."""

from typing import Any

import streamlit as st

from app.ui.input.field_metadata import (
    FIELD_GROUPS,
    build_scenario_data_table,
    format_field_description,
    format_field_label,
    get_credit_position_fields,
    get_credit_position_type_hints,
    get_field_default,
    get_field_unit,
    unwrap_optional,
)
from app.ui.responsive_table import render_responsive_position_table
from src.models.position import CreditPosition


def display_position_table(position: CreditPosition) -> None:
    """Render a CreditPosition using the responsive position-table renderer."""
    position_data = build_scenario_data_table(position)
    render_responsive_position_table(position_data)


def create_optional_numeric_field(
    field_name: str,
    label: str,
    resolved_type: Any,
    default: Any,
) -> Any:
    """Render an optional numeric field and return its current value."""
    provided_key = f"credit_position_{field_name}_provided"
    value_key = f"credit_position_{field_name}_value"

    provided = st.checkbox(
        f"Provide {label}",
        value=default is not None,
        key=provided_key,
    )

    if not provided:
        return None

    if resolved_type is int:
        value = st.number_input(
            label,
            value=(int(default) if default is not None else 0),
            step=1,
            key=value_key,
        )
        _render_field_metadata(field_name=field_name)
        return value

    if resolved_type is float:
        value = st.number_input(
            label,
            value=(float(default) if default is not None else 0.0),
            step=0.01,
            format="%.4f",
            key=value_key,
        )
        _render_field_metadata(field_name=field_name)
        return value

    raise TypeError(
        f"Unsupported optional numeric type: {field_name} -> {resolved_type}"
    )


def create_streamlit_field(field, field_type: Any) -> Any:
    """Render one CreditPosition field based on its resolved type."""
    field_name = field.name
    label = format_field_label(field_name)
    default = get_field_default(field)
    resolved_type, is_optional = unwrap_optional(field_type)

    if resolved_type is str and not is_optional:
        value = st.text_input(
            label,
            value=("" if default is None else str(default)),
            key=f"credit_position_{field_name}",
        )
        _render_field_metadata(field_name=field_name)
        return value

    if resolved_type is str and is_optional:
        provided = st.checkbox(
            f"Provide {label}",
            value=default is not None,
            key=f"credit_position_{field_name}_provided",
        )

        if not provided:
            return None

        value = st.text_input(
            label,
            value=("" if default is None else str(default)),
            key=f"credit_position_{field_name}_value",
        )
        _render_field_metadata(field_name=field_name)
        return value

    if resolved_type is int and not is_optional:
        value = st.number_input(
            label,
            value=(0 if default is None else int(default)),
            step=1,
            key=f"credit_position_{field_name}",
        )
        _render_field_metadata(field_name=field_name)
        return value

    if resolved_type is float and not is_optional:
        value = st.number_input(
            label,
            value=(0.0 if default is None else float(default)),
            step=0.01,
            format="%.4f",
            key=f"credit_position_{field_name}",
        )
        _render_field_metadata(field_name=field_name)
        return value

    if is_optional and resolved_type in {int, float}:
        return create_optional_numeric_field(
            field_name=field_name,
            label=label,
            resolved_type=resolved_type,
            default=default,
        )

    raise TypeError(
        f"Unsupported CreditPosition field type: {field_name} -> {field_type}"
    )


def _render_field_metadata(*, field_name: str) -> None:
    """Render compact description and unit metadata for one input field."""
    description = format_field_description(field_name)
    unit = get_field_unit(field_name)

    if unit:
        st.caption(f"{description} · Unit: {unit}")
    else:
        st.caption(description)


def _build_field_lookup() -> dict[str, Any]:
    """Build a lookup from field name to dataclass field."""
    return {field.name: field for field in get_credit_position_fields()}


def _render_field_group_header(group_title: str) -> None:
    """Render a compact visual header for an input group."""
    st.html(
        f"""
        <div class="input-group-header">
            <div class="input-group-title">
                {group_title}
            </div>
        </div>
        """
    )


def _render_field_group(
    *,
    group_title: str,
    field_names: list[str],
    field_lookup: dict[str, Any],
    type_hints: dict[str, Any],
    position_data: dict[str, Any],
) -> None:
    """Render one logical group of CreditPosition fields."""
    available_fields = [
        field_name for field_name in field_names if field_name in field_lookup
    ]

    if not available_fields:
        return

    _render_field_group_header(group_title)

    if group_title == "Identification":
        field_name = available_fields[0]
        position_data[field_name] = create_streamlit_field(
            field=field_lookup[field_name],
            field_type=type_hints[field_name],
        )
        return

    columns = st.columns(2, gap="medium")

    for index, field_name in enumerate(available_fields):
        with columns[index % 2]:
            position_data[field_name] = create_streamlit_field(
                field=field_lookup[field_name],
                field_type=type_hints[field_name],
            )


def _render_input_introduction() -> None:
    """Render the introduction card for manual CreditPosition input."""
    st.html(
        """
        <div class="input-introduction">
            <div class="input-introduction-title">
                Credit Position Data
            </div>
            <div class="input-introduction-description">
                Enter the financial information used by the
                deterministic assessment engine. The fields below
                correspond directly to the
                <strong>CreditPosition</strong> data model.
            </div>
            <div class="input-introduction-note">
                Assessment results are calculated separately by the
                deterministic rule engine and are not entered
                manually here.
            </div>
        </div>
        """
    )


def build_credit_position_from_ui() -> dict[str, Any]:
    """Build CreditPosition data from the Streamlit input UI."""
    model_fields = get_credit_position_fields()
    type_hints = get_credit_position_type_hints()
    field_lookup = _build_field_lookup()
    position_data: dict[str, Any] = {}

    _render_input_introduction()

    rendered_fields: set[str] = set()

    for group_title, field_names in FIELD_GROUPS.items():
        _render_field_group(
            group_title=group_title,
            field_names=field_names,
            field_lookup=field_lookup,
            type_hints=type_hints,
            position_data=position_data,
        )
        rendered_fields.update(
            field_name for field_name in field_names if field_name in field_lookup
        )

    ungrouped_fields = [
        field for field in model_fields if field.name not in rendered_fields
    ]

    if ungrouped_fields:
        _render_field_group(
            group_title="Additional Data",
            field_names=[field.name for field in ungrouped_fields],
            field_lookup=field_lookup,
            type_hints=type_hints,
            position_data=position_data,
        )

    return position_data
