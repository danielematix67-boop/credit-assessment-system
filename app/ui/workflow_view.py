import streamlit as st


def render_workflow_architecture() -> None:
    """
    Render the visual representation of the assessment workflow.

    This function is purely presentational.
    It does not execute any assessment logic.
    """

    st.subheader(
        "Assessment Workflow"
    )

    st.caption(
        "End-to-end processing architecture. Blue steps are fully "
        "deterministic; the violet step is where an LLM may "
        "generate prose, always constrained by the deterministic "
        "output next to it."
    )

    workflow_steps = [
        (
            "01",
            "Credit Data",
            "Structured financial input",
            "det",
        ),
        (
            "02",
            "Rule Engine",
            "Deterministic thresholds & severity",
            "det",
        ),
        (
            "03",
            "Analysis Agent",
            "Rule-based interpretation",
            "det",
        ),
        (
            "04",
            "Reporting Agent",
            "LLM-assisted prose with deterministic fallback",
            "ai",
        ),
        (
            "05",
            "Assessment Report",
            "Deterministic findings + executive summary",
            "det",
        ),
    ]

    pipeline_html = '<div class="pipeline-wrap">'

    for index, (
        number,
        title,
        description,
        kind,
    ) in enumerate(workflow_steps):

        pipeline_html += (
            f'<div class="pipeline-step {kind}">'
            f'<div class="pipeline-number">{number}</div>'
            f'<div class="pipeline-title">{title}</div>'
            f'<div class="pipeline-description">{description}</div>'
            f'</div>'
        )

        if index < len(workflow_steps) - 1:
            pipeline_html += (
                '<div class="pipeline-arrow">→</div>'
            )

    pipeline_html += "</div>"

    st.markdown(
        pipeline_html,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pipeline-legend">
            <div class="pipeline-legend-item">
                <span class="legend-dot det"></span> Deterministic
            </div>
            <div class="pipeline-legend-item">
                <span class="legend-dot ai"></span> AI-assisted
                (with deterministic fallback)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )