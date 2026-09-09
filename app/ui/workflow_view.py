import streamlit as st


def render_workflow_architecture() -> None:
    """
    Render a compact visual representation of the assessment workflow.

    This function is purely presentational.
    It does not execute any assessment logic.
    """

    with st.expander("How the assessment works", expanded=False):
        st.caption(
            "The workflow separates deterministic credit assessment from optional "
            "AI-assisted reporting. Only the Rule Engine can determine the assessment."
        )

        workflow_steps = [
            ("01", "Credit Data", "Financial input", "det"),
            ("02", "Rule Engine", "Rules & thresholds", "det"),
            ("03", "Analysis", "Structured findings", "det"),
            ("04", "Reporting", "AI-assisted narrative", "ai"),
            ("05", "Assessment Report", "Decision + evidence", "det"),
        ]

        pipeline_html = '<div class="pipeline-wrap">'

        for index, (number, title, description, kind) in enumerate(workflow_steps):
            pipeline_html += (
                f'<div class="pipeline-step {kind}">'
                f'<div class="pipeline-number">{number}</div>'
                f'<div class="pipeline-title">{title}</div>'
                f'<div class="pipeline-description">{description}</div>'
                f"</div>"
            )

            if index < len(workflow_steps) - 1:
                pipeline_html += '<div class="pipeline-arrow">→</div>'

        pipeline_html += "</div>"

        st.markdown(pipeline_html, unsafe_allow_html=True)

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
