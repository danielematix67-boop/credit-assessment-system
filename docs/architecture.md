# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment application with an optional AI-assisted reporting layer.

The architecture separates three responsibilities:

1. **Assessment** — deterministic evaluation of financial indicators and business rules.
2. **Analysis** — structured organization of deterministic findings.
3. **Reporting** — generation of a human-readable Executive Report, optionally using an LLM.

The central boundary is:

> **The deterministic assessment is the source of truth. The LLM is an optional reporting component and has no decision authority.**

The repository keeps framework-independent logic under `src/` and the Streamlit presentation layer under `app/`.

---

## 2. Architectural Principles

| Principle | Implementation |
|---|---|
| Deterministic decision authority | Rule results and assessment status are calculated without an LLM. |
| Separation of concerns | Assessment, analysis and reporting are separate workflow stages. |
| Configuration-driven rules | Thresholds and severity parameters are externalized in `config/rules.yaml`. |
| Pluggable rules | Rules are discovered and resolved through a registry using `rule_id`. |
| Provider independence | Gemini and Ollama are accessed through the `LLMClient` abstraction. |
| Graceful degradation | LLM reporting can fall back to deterministic reporting. |
| Grounded narrative generation | LLM prompts and optional response validation constrain narrative output to supplied evidence. |
| Execution observability | Provenance, fallback state, error classification and timings are exposed separately from decision data. |
| Immutable state | Core assessment, analysis, report and execution metadata use immutable dataclasses where appropriate. |
| UI/domain decoupling | Streamlit presentation code does not own credit-risk business rules. |

---

## 3. System Architecture

```text
CreditPosition
      │
      ▼
AssessmentService
      │
      ├── RuleEngine → RuleResult[]
      ├── CommentEngine → RuleFinding[]
      └── StatusCalculator → Assessment
                                  │
                                  ▼
                           AnalysisAgent
                                  │
                                  ▼
                         AssessmentAnalysis
                                  │
                                  ▼
                          ReportingAgent
                           /             \\
                          /               \\
       DeterministicReportGenerator   LLMReportGenerator
                          \               /
                           \             /
                                Report
                                  │
                                  ▼
                         ExecutionMetadata
```

The complete workflow is coordinated by `AssessmentWorkflow` and exposed through the orchestration layer.

### Dependency direction

```text
Streamlit (`app/`)
       ↓
Application / Orchestration
       ↓
Services / Agents
       ↓
Rules / Domain Models
```

The core library does not depend on Streamlit.

---

## 4. Presentation Layer — `app/`

The Streamlit application is responsible for input collection, reporting-mode selection, workflow execution and presentation of domain results.

Key components include:

- `app/streamlit_app.py` — entry point;
- `app/ui/input_source.py` — credit-position input;
- `app/ui/assessment_configuration.py` — assessment configuration and run action;
- `app/ui/results.py` — operator-oriented results composition;
- `app/ui/report.py` — Executive Report presentation;
- `app/ui/charts.py` — decision-path and risk-indicator visualisations;
- `app/ui/workflow_view.py` — compact workflow explanation;
- `app/workflow/` — application-level workflow composition and execution wrapper.

The UI consumes `AssessmentWorkflowResult` and `RuleResult` objects rather than reimplementing business logic.

### Current Results hierarchy

The Results view is intentionally organized from the executive outcome toward deeper evidence:

```text
Executive Credit Assessment
          ↓
Assessment Overview
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The hierarchy keeps the primary report concise while making deterministic evidence available on demand.

### Decision Path

The Results UI includes a graphical three-stage decision path:

```text
Financial Indicators
        ↓
Rule Engine Outcomes
        ↓
Monitoring Assessment
```

The visualization dynamically shows the number of rules evaluated, triggered rules and non-evaluable rules, together with the final assessment status and the relevant triggered-rule chips.

The Decision Path is explanatory only. It consumes the outputs of the deterministic assessment and does not recalculate thresholds, severity or status.

### Risk Indicator Dashboard

`render_risk_indicator_dashboard()` provides the detailed rule-evidence surface. It includes:

- KPI counts for indicators, triggered rules, high/critical severity and non-evaluable rules;
- rule-outcome distribution;
- severity profile;
- filterable Rule Catalogue;
- filtering by status, severity and category;
- priority-oriented sorting;
- individual rule inspection.

The individual rule detail view presents:

```text
Rule ID / Category
        ↓
Indicator
        ↓
Observed Value vs Configured Threshold
        ↓
Status / Severity / Direction
        ↓
Rationale
```

The dashboard is presentation-only and reads deterministic `RuleResult` fields directly. It does not duplicate rule calculations.

### Audit Trail

The audit area contains broader traceability information:

- Decision Path;
- complete rule evidence;
- credit data used;
- methodology;
- execution metadata.

This replaces the need for multiple overlapping evidence surfaces and keeps detailed diagnostics in one coherent area.

---

## 5. Assessment Layer

`AssessmentService` owns the deterministic assessment stage:

```text
CreditPosition
      ↓
RuleEngine.evaluate()
      ↓
RuleResult[]
      ↓
CommentEngine
      ↓
RuleFinding[]
      ↓
AssessmentStatusCalculator
      ↓
Assessment
```

The service determines rule outcomes, findings and the overall assessment status. No LLM is involved in this path.

The domain model `Assessment` contains:

- `position_id`;
- `rule_results`;
- `findings`;
- `status`.

---

## 6. Rule Engine

Rules implement a common abstraction and are resolved through the rule registry.

```text
Rule.evaluate(position) → RuleResult
```

The current configured rule catalogue contains revenue, profitability, leverage and interest-coverage indicators.

### Configuration

Rule parameters are externalized in:

```text
config/rules.yaml
```

Configuration includes rule identifiers, names, categories, trigger thresholds, severity and severity direction, with optional graduated severity thresholds.

### Discovery

The registry/discovery mechanism connects configured `rule_id` values to concrete implementations. The central assessment service therefore does not require a growing rule-specific dispatcher.

---

## 7. Analysis Layer

`AnalysisAgent` converts `Assessment` into `AssessmentAnalysis`.

```text
Assessment
    ↓
AnalysisAgent
    ↓
AssessmentAnalysis
```

The analysis layer organizes deterministic information into:

- key findings;
- risk factors;
- limitations;
- assessment status.

It does not perform a second credit assessment. The invariant is:

```text
Assessment.status
      =
AssessmentAnalysis.assessment_status
```

---

## 8. Reporting Layer

`ReportingAgent` converts `AssessmentAnalysis` into a `Report`.

Supported generators are:

```text
DeterministicReportGenerator
          OR
LLMReportGenerator
```

The report model contains the deterministic assessment status, executive summary, grouped findings and limitations.

### Executive Report contract

The Streamlit report presentation exposes the deterministic status first and then the narrative. For LLM-assisted reporting the conceptual output is:

```text
Assessment Status: Critical

LLM-generated executive narrative
```

The status is constructed from application-controlled assessment data. The LLM does not generate or determine it.

---

## 9. LLM Architecture

### Provider abstraction

LLM access is hidden behind `LLMClient`:

```text
LLMClient
   ├── GeminiClient
   ├── OllamaClient
   └── MockLLMClient
```

The reporting domain therefore remains independent from a concrete provider SDK.

### Prompt contract

The prompt builder receives deterministic findings and explicitly constrains the model to narrative generation.

The current reporting contract requires the model to:

- represent all supplied material findings;
- preserve numerical indicator values and units exactly;
- avoid unsupported facts and causal explanations;
- avoid inventing sales volume, pricing, demand, costs, liquidity, cash flow, debt service capacity or financial stability unless provided;
- preserve category order;
- discuss each category at most once;
- avoid category headings and list-like output;
- mention each material indicator value once;
- avoid repeating findings or conclusions;
- end after the final material finding;
- never generate the assessment status.

### Indicator grounding validation

`LLMReportGenerator` can run in strict indicator-grounding mode. In that mode, deterministic indicator values extracted from the supplied findings must be represented in the generated narrative.

If a required indicator is missing, the generator falls back to `DeterministicReportGenerator`.

This creates an additional safety boundary between deterministic evidence and generated prose:

```text
Deterministic findings
        ↓
Prompt contract
        ↓
LLM narrative
        ↓
Grounding validation
     /       \\
   valid    invalid
     ↓         ↓
  Narrative  Deterministic fallback
```

The validation is deliberately narrow: it protects required numerical evidence but does not attempt to perform full semantic verification of arbitrary natural language.

---

## 10. Reliability and Failure Handling

```text
Primary Generator
      │
 ┌────┴────┐
Success   Failure
   │         │
 Report   Error Classification
             │
             ▼
   Deterministic Fallback
          │
     ┌────┴────┐
  Success    Failure
     │           │
   Report     Propagate Error
```

Operational categories include `RATE_LIMIT`, `SERVICE_UNAVAILABLE`, `CONNECTION_ERROR`, `AUTHENTICATION`, `AUTHORIZATION`, `MODEL_UNAVAILABLE`, `TIMEOUT` and `GENERATION_ERROR`.

Fallback affects only report generation. It does not modify the deterministic assessment.

If both primary and fallback generation fail, the terminal error is propagated.

---

## 11. Execution Observability

`AssessmentWorkflowResult` exposes immutable execution information alongside the assessment, analysis and report.

The execution metadata includes:

- unique execution ID;
- UTC start timestamp;
- reporting mode;
- generator used;
- fallback state;
- classified reporting error category when applicable;
- assessment, analysis, reporting and total elapsed time.

Conceptually:

```text
Workflow Execution
        ↓
ExecutionMetadata
 ├── Identity
 ├── Timestamp
 ├── Reporting provenance
 ├── Error classification
 └── Phase timings
```

The UI exposes this information in the audit area rather than mixing it into the primary credit judgement.

---

## 12. Domain Model

The main workflow objects are:

| Model | Responsibility |
|---|---|
| `CreditPosition` | Financial input to be assessed. |
| `RuleResult` | Result of one deterministic rule evaluation. |
| `RuleFinding` | Structured triggered-rule finding. |
| `Assessment` | Complete deterministic assessment. |
| `AnalysisFinding` | Normalized finding used by analysis/reporting. |
| `AssessmentAnalysis` | Structured analysis of deterministic evidence. |
| `Report` | Final report including deterministic status and narrative. |
| `ExecutionMetadata` | Immutable execution provenance and timings. |
| `AssessmentWorkflowResult` | Complete workflow output. |

The use of explicit domain objects prevents downstream presentation or reporting components from silently mutating decision data.

---

## 13. Repository Structure

```text
credit-assessment-system/
├── app/                         # Streamlit presentation layer
│   ├── streamlit_app.py
│   ├── ui/
│   └── workflow/
├── config/
│   └── rules.yaml
├── src/
│   ├── agents/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   ├── orchestration/
│   ├── rules/
│   └── services/
├── docs/
└── tests/
```

---

## 14. Extension Points

### Add a new rule

1. Implement the common rule abstraction.
2. Register the rule with a unique `rule_id`.
3. Add its parameters to `config/rules.yaml`.
4. Add unit tests.

The central assessment workflow does not need rule-specific branching.

### Add a new LLM provider

Implement `LLMClient` and inject the provider through the existing reporting workflow. The deterministic assessment remains unchanged.

### Add a new report generator

Implement the report-generation abstraction and consume the existing `AssessmentAnalysis`. The new generator remains downstream of the deterministic assessment.

---

## 15. Architectural Boundary

The complete system can be summarized as:

```text
                 DETERMINISTIC CORE
                       │
                       ▼
                 Rule Evaluation
                       │
                       ▼
                 Assessment Status
                       │
                       ▼
                Structured Analysis
                       │
              ┌────────┴────────┐
              ▼                 ▼
      Deterministic         LLM-assisted
         Report               Report
              │                 │
              └────────┬────────┘
                       ▼
                    Executive
                      Report
```

The LLM is therefore an optional, replaceable and bounded reporting dependency rather than part of the credit decision itself.

For the rationale and trade-offs behind these decisions, see [`architecture-decisions.md`](architecture-decisions.md).
