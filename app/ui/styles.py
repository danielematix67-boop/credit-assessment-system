import streamlit as st

# ============================================================
# Styling
# ============================================================
#
# Design language:
#   - "Deterministic" surfaces use the BLUE accent (--det-color).
#     These are surfaces produced exclusively by the rule engine
#     / analysis agent and are fully reproducible & traceable.
#   - "AI-assisted" surfaces use the VIOLET accent (--ai-color).
#     These are surfaces where an LLM (Gemini or Ollama) produced
#     natural-language text on top of the deterministic findings.
#   - "Fallback" surfaces use the AMBER accent (--fallback-color).
#     These indicate the LLM was requested but unavailable, so the
#     deterministic generator produced the report instead.
#
# Every card/badge in the app consistently reuses these three
# colors so the provenance of any piece of content is recognizable
# at a glance, without reading the fine print.


def apply_styles() -> None:
    st.markdown(
        """
        <style>

        :root {
            --det-color: #2563eb;
            --det-bg: rgba(37, 99, 235, 0.08);
            --ai-color: #7c3aed;
            --ai-bg: rgba(124, 58, 237, 0.08);
            --fallback-color: #b45309;
            --fallback-bg: rgba(180, 83, 9, 0.10);
            --muted: #6b7280;
            --border: rgba(128, 128, 128, 0.20);
        }

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        h1, h2, h3 {
            letter-spacing: -0.01em;
        }

        .app-subtitle {
            color: var(--muted);
            font-size: 1rem;
            margin-top: -0.4rem;
            margin-bottom: 1.2rem;
        }

        /* ---------------------------------------------------- */
        /* Provenance badges                                     */
        /* ---------------------------------------------------- */

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.22rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 650;
            letter-spacing: 0.01em;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .badge-det {
            color: var(--det-color);
            background: var(--det-bg);
            border-color: rgba(37, 99, 235, 0.25);
        }

        .badge-ai {
            color: var(--ai-color);
            background: var(--ai-bg);
            border-color: rgba(124, 58, 237, 0.25);
        }

        .badge-fallback {
            color: var(--fallback-color);
            background: var(--fallback-bg);
            border-color: rgba(180, 83, 9, 0.28);
        }

        .badge-row {
            margin-bottom: 0.6rem;
        }

        /* ---------------------------------------------------- */
        /* Pipeline / workflow diagram                           */
        /* ---------------------------------------------------- */

        .pipeline-wrap {
            display: flex;
            align-items: stretch;
            gap: 0.4rem;
            margin: 0.4rem 0 0.8rem 0;
        }

        .pipeline-step {
            flex: 1;
            padding: 1rem 0.9rem;
            border-radius: 0.7rem;
            border: 1.5px solid var(--border);
            background: rgba(128, 128, 128, 0.025);
            min-height: 108px;
            position: relative;
        }

        .pipeline-step.det {
            border-color: rgba(37, 99, 235, 0.35);
            background: var(--det-bg);
        }

        .pipeline-step.ai {
            border-color: rgba(124, 58, 237, 0.35);
            background: var(--ai-bg);
        }

        .pipeline-arrow {
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 1.1rem;
            padding: 0 0.1rem;
        }

        .pipeline-number {
            font-size: 0.72rem;
            font-weight: 750;
            color: var(--muted);
            letter-spacing: 0.06em;
        }

        .pipeline-title {
            font-weight: 650;
            margin-top: 0.25rem;
            font-size: 0.92rem;
        }

        .pipeline-description {
            color: var(--muted);
            font-size: 0.76rem;
            margin-top: 0.1rem;
            line-height: 1.35;
        }

        .pipeline-legend {
            display: flex;
            gap: 1.4rem;
            margin-top: 0.4rem;
            margin-bottom: 0.2rem;
            flex-wrap: wrap;
        }

        .pipeline-legend-item {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.78rem;
            color: var(--muted);
        }

        .legend-dot {
            width: 0.65rem;
            height: 0.65rem;
            border-radius: 50%;
            display: inline-block;
        }

        .legend-dot.det { background: var(--det-color); }
        .legend-dot.ai { background: var(--ai-color); }

        /* ---------------------------------------------------- */
        /* Generic cards                                          */
        /* ---------------------------------------------------- */

        .scenario-card {
            padding: 1.2rem 1.4rem;
            border-radius: 0.7rem;
            border: 1px solid var(--border);
            background: rgba(128, 128, 128, 0.025);
            margin-bottom: 1rem;
        }

        .scenario-title {
            font-size: 1.1rem;
            font-weight: 650;
            margin-bottom: 0.4rem;
        }

        .scenario-description {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.5;
        }

        .data-introduction {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.5;
            margin-bottom: 1rem;
        }

        .data-note {
            padding: 0.9rem 1rem;
            border-radius: 0.6rem;
            border: 1px solid var(--border);
            background: rgba(128, 128, 128, 0.025);
            margin-bottom: 1rem;
            font-size: 0.85rem;
            color: var(--muted);
        }

        .provenance-panel {
            border-radius: 0.75rem;
            border: 1px solid var(--border);
            padding: 1.1rem 1.3rem;
            margin-bottom: 1.2rem;
            background: rgba(128, 128, 128, 0.02);
        }

        .provenance-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.45rem 0;
            border-bottom: 1px dashed var(--border);
            font-size: 0.87rem;
        }

        .provenance-row:last-child {
            border-bottom: none;
        }

        .provenance-label {
            color: inherit;
            font-weight: 550;
        }

        .metric-description {
            color: var(--muted);
            font-size: 0.78rem;
        }

        .section-card {
            border-radius: 0.7rem;
            border: 1.5px solid var(--border);
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }

        .section-card.det {
            border-left: 4px solid var(--det-color);
        }

        .section-card.ai {
            border-left: 4px solid var(--ai-color);
        }

        .section-card.fallback {
            border-left: 4px solid var(--fallback-color);
        }

        .footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.78rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )



