# Application Layer: Streamlit UI and Orchestration

This document describes the responsibilities of the current `app/` package. The implementation is the source of truth; this guide distinguishes the active Streamlit execution path from modules that remain in the repository but are not called by the current entry point.

## Responsibility boundary

`app/` is the user-facing adapter around the assessment system. It handles Streamlit page composition, user input, provider configuration, workflow construction, session state and presentation. It does not implement credit-risk thresholds, rule evaluation, section aggregation or final-assessment policy; those responsibilities remain in `src/` and `config/`.

```text
Streamlit entry point
       |
       +--> UI input and reporting-mode selection
       |
       +--> application workflow factory
       |
       +--> workflow runner
       |
       +--> deterministic assessment / analysis / reporting in src/
       |
       +--> store workflow result in session state
       |
       +--> render result and narrative
```

## Active entry point

`app/streamlit_app.py` is the composition root. It configures the Streamlit page, applies styles and design tokens, renders the sidebar/header/workflow overview, obtains the workbook input, displays the assessment action, executes the workflow when requested, stores the result and renders the latest result from session state.

The entry point delegates to focused modules rather than implementing the workflow inline:

| Module | Responsibility |
|---|---|
| `app/ui/layout.py` | Header and footer |
| `app/ui/styles.py`, `design_tokens.py` | Global styling and semantic design tokens |
| `app/ui/sidebar.py` | Reporting-mode selection |
| `app/ui/workflow_view.py` | Workflow architecture explainer |
| `app/ui/input_source.py` | Workbook upload, scenario selection, input preview and domain-data session state |
| `app/ui/assessment_configuration.py` | Run Assessment action |
| `app/ui/assessment.py` | Position hand-off, workflow execution and result/session-state storage |
| `app/ui/results/` | Result summary, deterministic evidence dashboard and Executive Narrative |

## Input path

The current entry point calls `render_credit_data_source()`, which delegates to the Excel upload path. The active Streamlit input source is therefore **Excel Upload**:

1. The user uploads an `.xlsx` workbook.
2. `load_excel_scenarios()` validates and maps workbook content to domain models.
3. The user selects one of the loaded scenarios.
4. The UI previews Customer Profile, Financial Analysis, Behavioural Analysis and Debt Sustainability data.
5. The optional domain objects are stored in Streamlit session state and passed to the workflow runner with the financial `CreditPosition`.

The workbook contract, required/optional sheets and field-level rules are documented in [Excel Scenario Input](excel-scenario-input.md).

### Modules not used by the current input screen

The repository also contains `app/ui/input/credit_position.py`, which provides generic/manual Streamlit field rendering, and `app/demo_scenarios.py`, which defines a synthetic in-code demo catalogue. Neither is called by the current `streamlit_app.py` input path. The live input screen explicitly describes the uploaded workbook as its single source of demonstration data. Their presence in the repository must not be interpreted as evidence that manual entry or the in-code demo selector is currently exposed to users.

## Reporting configuration

`app/config.py` detects the Streamlit Cloud environment, reads secrets safely and resolves provider configuration.

- Gemini API key: Streamlit secrets first, then `GEMINI_API_KEY` environment variable.
- Ollama host/model: `[ollama]` Streamlit secrets first, then `OLLAMA_HOST` / `OLLAMA_MODEL`, then local defaults.
- Reporting modes: Deterministic and Gemini + Fallback are exposed in Streamlit Cloud; local execution also exposes Ollama + Fallback.

The sidebar chooses the narrative-generation mode. It does not select a credit-decision engine: every mode constructs the same deterministic assessment path.

## Workflow construction and execution

`app/workflow/assessment_workflow_factory.py` assembles the assessment service, case-analysis agent and reporting components. It selects one of three reporting configurations:

- Deterministic generator only.
- Gemini-backed LLM generator with deterministic fallback.
- Ollama-backed LLM generator with deterministic fallback.

The LLM generator is configured to require indicator values. Provider credentials and host/model settings are resolved through `app/config.py`.

`app/workflow/runner.py` is the thin application adapter that forwards the position and optional domain data to the workflow. `app/ui/assessment.py` creates the workflow, runs it under a Streamlit spinner, handles application-level errors and stores the successful result.

## Session state

The current UI stores the latest result and its associated position, input mode, reporting mode and scenario name in `st.session_state`. The optional Customer Profile, Behavioural Analysis and Debt Sustainability objects are also placed in session state by the input screen and read when the workflow runs.

This supports Streamlit reruns and redisplay of the latest completed result. It is not persistent assessment history, database storage or an audit-trail service.

## Results presentation

The active results composition is `app/ui/results/page.py`, called through the results package. It renders:

- the final assessment status and counts derived from the returned rule evidence;
- the deterministic `status_rationale` and contributing risk areas from `FinalAssessment`;
- reporting provenance and fallback information;
- the macro-area risk-indicator dashboard;
- the Executive Narrative.

Presentation code may count, filter, sort and format existing evidence for display. It must not recalculate rule outcomes, thresholds, severity, section status or final status. The UI is a read-only consumer of the structured workflow result.

The detailed Behavioural Analysis view may show the optional Centrale dei Rischi exposure snapshot as context. Those amounts do not become behavioural rule findings or affect assessment status; see [Behavioural Analysis](behavioural-analysis.md).

## Error handling

Workflow construction and execution errors are surfaced in Streamlit and stop the current run. Provider/report-generation failures may be handled within the reporting layer by the configured deterministic fallback. A reporting failure must not cause the application to recalculate or replace the deterministic credit assessment.

## Change guidance

When modifying the application:

- keep credit-risk calculations and decision policy in `src/` and `config/`;
- keep Streamlit controls, page composition and rendering in `app/ui/`;
- keep provider selection and workflow assembly in `app/config.py` and `app/workflow/`;
- preserve structured domain inputs and workflow outputs across the boundary;
- update this document when the active input path, reporting modes, orchestration or visible results change;
- add or update focused tests under `tests/app/` and workflow/integration tests when a change crosses application and core boundaries.
