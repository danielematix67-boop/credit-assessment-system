# Application Workflow and Streamlit Interface

This document describes the current application path implemented under `app/` and the workflow orchestration under `src/agents/workflow/`.

## Application entry point

The Streamlit entry point is `app/streamlit_app.py`. It configures the page, applies styles, renders the sidebar and header, shows the workflow overview, obtains the selected input source, renders the Run Assessment action, executes the workflow when requested, stores the latest result in Streamlit session state, and renders the results.

The application is a presentation and orchestration layer. It delegates assessment and reporting to the workflow and services in `src/`.

## Current input experience

The current Streamlit input source is a single complete synthetic demonstration case, named **Complete Credit Assessment**. It supplies inputs for all four assessment areas:

- Customer Profile
- Financial Analysis
- Behavioural Analysis
- Debt Sustainability

The page shows domain availability and provides expandable, tabbed previews of the synthetic input objects. The scenario is defined in `app/demo_scenarios.py`; its inputs are constructed as `CreditPosition`, `CustomerProfileData`, `BehaviouralData` and `DebtSustainabilityData` objects.

Although parts of the application retain helper functions and state keys for manual input, the current input-source renderer selects the demo scenario. The presence of those helpers should not be interpreted as a currently exposed, complete manual-entry workflow.

## Reporting modes

The sidebar exposes the reporting mode used to construct the workflow:

- **Deterministic** — uses `DeterministicReportGenerator` without an LLM.
- **Gemini + Fallback** — uses the Gemini-backed `LLMReportGenerator` and the deterministic generator as fallback. A Gemini API key is required.
- **Ollama + Fallback** — uses the Ollama-backed `LLMReportGenerator` and deterministic fallback. Host and model configuration are required.

These modes affect report generation only. All modes execute the deterministic assessment first. Provider configuration is read through `app/config.py` and may be supplied through deployment/environment settings.

## Execution sequence

The application calls `execute_assessment()`, which creates a workflow through `app/workflow/assessment_workflow_factory.py` and invokes `app/workflow/runner.py`.

The workflow in `src/agents/workflow/assessment_workflow.py` performs these steps in order:

1. Generate execution identity and capture start time.
2. Run `CreditAssessmentCaseService.assess()` with the position and domain inputs.
3. Run `CaseAnalysisAgent` on the resulting credit case.
4. Run `ReportingAgent` on the structured analysis.
5. Capture generator/fallback information and elapsed times.
6. Return an `AssessmentWorkflowResult` containing the case, analysis, report and execution metadata.

The reporting stage is downstream of assessment and analysis. A provider or report-generation issue does not recalculate the deterministic case result.

## Results presentation

The results package under `app/ui/results/` renders the stored workflow result. The current experience includes:

- an executive assessment header and summary metrics;
- reporting provenance, including selected mode and fallback information when available;
- final assessment and macro-area statuses, evidence counts and limitations;
- a deterministic Rule Engine evidence dashboard with macro-area cards;
- filters for rule status, severity, assessment area and sort order;
- individual rule details and indicator/evidence views;
- the Executive Narrative.

The UI derives its display from the workflow result. It may count or format evidence for presentation, but it does not recalculate thresholds, rule severity, section status or final assessment.

## Session state and reruns

After a successful run, the application stores the latest workflow result, position, input mode and reporting mode in Streamlit session state. The results view reads this stored result, allowing the page to render the latest completed assessment across Streamlit reruns.

The application currently demonstrates a single latest result in the session. This is not a persistent assessment-history or audit-trail implementation.

## Error handling

Workflow construction and assessment execution are wrapped in application-level error handling. Errors are displayed in the Streamlit interface and stop the current execution path. Reporting-provider errors may instead be handled by `ReportingAgent` and its configured deterministic fallback, depending on the selected mode and failure type.

## Extension guidance

When changing the application experience:

- keep deterministic business logic in `src/`;
- keep Streamlit controls and rendering in `app/ui/`;
- keep application workflow construction in `app/workflow/`;
- pass structured domain inputs into the workflow rather than duplicating assessment calculations in the UI;
- update synthetic demo data when the input contract changes;
- test both workflow behaviour and display behaviour where the change crosses those boundaries;
- update this document when the user-visible input, reporting modes, execution sequence or results layout changes.
