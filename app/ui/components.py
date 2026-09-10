import streamlit as st

from app.ui.design_tokens import (
    FALLBACK_BG,
    FALLBACK_COLOR,
    MUTED_BG,
    MUTED_COLOR,
    NORMAL_BG,
    NORMAL_COLOR,
)

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
# Assessment Status
# ============================================================


def render_assessment_status(status: str) -> None:
    """Render the deterministic assessment status as a reusable badge."""
    normalized = status.upper().replace(" ", "_")
    palette = {
        "CRITICAL": (FALLBACK_COLOR, FALLBACK_BG),
        "ATTENTION": (FALLBACK_COLOR, FALLBACK_BG),
        "NORMAL": (NORMAL_COLOR, NORMAL_BG),
    }
    foreground, background = palette.get(
        normalized,
        (MUTED_COLOR, MUTED_BG),
    )
    label = normalized.replace("_", " ").title()

    st.markdown(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            padding:0.24rem 0.72rem;
            border-radius:999px;
            border:1px solid {foreground}55;
            background:{background};
            color:{foreground};
            font-size:0.78rem;
            font-weight:750;
            letter-spacing:0.02em;
        ">{label}</span>
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
    Map a reporting mode selection to its intended badge kind,
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
    """Render the selected demo scenario."""
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
