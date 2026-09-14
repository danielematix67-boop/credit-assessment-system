import streamlit as st


def render_workflow_architecture() -> None:
    """Show the assessment methodology as a persistent section."""
    st.subheader("How the assessment works")
    st.caption(
        "Credit data → deterministic Rule Engine → monitoring judgement → executive report."
    )

    workflow_steps = [
        ("01", "Credit data", "Input", "det"),
        ("02", "Rule Engine", "Thresholds & outcomes", "det"),
        ("03", "Judgement", "Risk & severity", "det"),
        ("04", "Report", "Narrative", "ai"),
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
        "The Rule Engine is the sole source of the deterministic assessment. "
        "AI only supports narrative generation and cannot change the judgement."
    )
