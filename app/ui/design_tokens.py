"""Shared design tokens for the Credit Assessment System UI.

These values are presentation-only. They do not affect credit assessment
logic, rule thresholds, severity, or decisions.
"""

DET_COLOR = "#2563eb"
DET_BG = "rgba(37, 99, 235, 0.08)"
AI_COLOR = "#7c3aed"
AI_BG = "rgba(124, 58, 237, 0.08)"
FALLBACK_COLOR = "#b45309"
FALLBACK_BG = "rgba(180, 83, 9, 0.10)"
NORMAL_COLOR = "#166534"
NORMAL_BG = "rgba(22, 101, 52, 0.10)"
MUTED_COLOR = "#6b7280"
MUTED_BG = "rgba(107, 114, 128, 0.10)"


def css_variables() -> str:
    """Return the canonical CSS variable declarations."""
    return f"""
        :root {{
            --det-color: {DET_COLOR};
            --det-bg: {DET_BG};
            --ai-color: {AI_COLOR};
            --ai-bg: {AI_BG};
            --fallback-color: {FALLBACK_COLOR};
            --fallback-bg: {FALLBACK_BG};
            --muted: {MUTED_COLOR};
        }}
    """
