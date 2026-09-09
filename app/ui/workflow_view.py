import streamlit as st


def render_workflow_architecture() -> None:
    """Show the credit-monitoring workflow in one compact view."""
    with st.expander("How the monitoring assessment works", expanded=False):
        st.caption(
            "The workflow shows how raw credit information becomes a documented "
            "monitoring judgement and executive report."
        )

        workflow_steps = [
            ("01", "Credit Position", "Data & information", "det"),
            ("02", "Financial Indicators", "Actual values", "det"),
            ("03", "Rule Engine", "Thresholds & outcomes", "det"),
            ("04", "Monitoring Judgement", "Risk & severity", "det"),
            ("05", "Executive Report", "Decision & rationale", "ai"),
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
            "The Rule Engine owns the deterministic judgement, rule outcomes, "
            "severity and thresholds. The Analysis layer organises the findings. "
            "AI is used only for report narrative and cannot change the judgement."
        )
