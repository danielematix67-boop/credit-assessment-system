import streamlit as st


def render_workflow_architecture() -> None:
    """Show the assessment pipeline in one compact view."""
    with st.expander("How the assessment works", expanded=False):
        st.caption(
            "The system first determines the credit assessment deterministically, "
            "then converts the structured result into the Executive Report."
        )

        workflow_steps = [
            ("01", "Credit Data", "Financial input", "det"),
            ("02", "Rule Engine", "Rules & thresholds", "det"),
            ("03", "Analysis", "Risk findings", "det"),
            ("04", "Executive Report", "Deterministic / Gemini / Ollama", "ai"),
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
        st.caption(
            "The Rule Engine is the sole authority for assessment status, severity and thresholds. "
            "LLMs only generate the report narrative and cannot change the decision."
        )
