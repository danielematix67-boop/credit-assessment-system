import streamlit as st

# ============================================================
# Shared UI Components
# ============================================================


def render_section_header(title: str, description: str) -> None:
    """Render a consistent visual section header."""
    st.markdown(
        f"""
        <div class="ui-section-header">
            <div class="ui-section-title">{title}</div>
            <div class="ui-section-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Badge / Provenance Helpers
# ============================================================


def render_badge(
    label: str,
    kind: str = "det",
) -> str:
    """
    Return the HTML markup for a small provenance badge.

    kind: "det" | "ai" | "fallback"
    """

    icons = {
        "det": "🔒",
        "ai": "🤖",
        "fallback": "⚠️",
    }

    css_class = {
        "det": "badge-det",
        "ai": "badge-ai",
        "fallback": "badge-fallback",
    }[kind]

    icon = icons[kind]

    return f'<span class="badge {css_class}">{icon} {label}</span>'


def show_badge(
    label: str,
    kind: str = "det",
) -> None:
    st.markdown(
        f'<div class="badge-row">{render_badge(label, kind)}</div>',
        unsafe_allow_html=True,
    )


def reporting_mode_badge_kind(
    reporting_mode: str,
) -> str:
    """
    Map a reporting mode selection to its *intended* badge kind,
    before knowing whether a fallback actually occurred.
    """

    if reporting_mode == "Deterministic":
        return "det"

    return "ai"


# ============================================================
# Scenario Card
# ============================================================


def render_scenario_card(
    scenario_name: str,
    description: str,
) -> None:
    """
    Render the selected demo scenario.
    """

    st.markdown(
        f"""
        <div class="scenario-card">
            <div class="scenario-title">
                {scenario_name}
            </div>
            <div class="scenario-description">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
