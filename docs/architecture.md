# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment application with an optional AI-assisted reporting layer.

The architecture separates four responsibilities:

1. **Input Validation** — structural validation of the incoming credit position.
2. **Assessment** — deterministic evaluation of financial indicators and business rules.
3. **Analysis** — structured organization of deterministic findings.
4. **Reporting** — generation of a human-readable Executive Report, optionally using an LLM.

The central boundary is:

> **The deterministic assessment is the source of truth. The LLM is an optional reporting component and has no decision authority.**

The repository keeps framework-independent logic under `src/` and the Streamlit presentation layer under `app/`.

---

## 2. Architectural Principles

| Principle | Implementation |
|---|---|
| Structural input validation | `CreditPositionValidator` rejects malformed positions before rule evaluation. |
| Deterministic decision authority | Rule results and assessment status are calculated without an LLM. |
| Separation of concerns | Validation, assessment, analysis and reporting are separate responsibilities. |
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
CreditPositionValidator
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

## 4. Input Validation Layer

`CreditPositionValidator` performs structural validation before deterministic assessment begins.

The validator checks:

- the object is a `CreditPosition`;
- `position_id` is non-empty;
- numeric financial fields contain numeric values or `None`;
- boolean values are not accepted as numeric inputs;
- numeric values are finite, rejecting `NaN` and positive/negative infinity.

`None` is intentionally accepted because unavailable financial information is a valid domain condition and can subsequently produce `NOT_EVALUABLE` rule outcomes.

The validator does not impose business-specific sign constraints. For example, whether a negative value is economically meaningful is the responsibility of the corresponding deterministic rule, not of the generic structural validator.

```text
CreditPosition
      ↓
Structural validation
   /          \\
valid        invalid
  ↓              ↓
Rule Engine   ValueError / TypeError
```

This establishes a clear boundary between **input integrity** and **credit-risk business semantics**.

---

## 5. Presentation Layer — `app/`

The Streamlit application is responsible for input collection, reporting-mode selection, workflow execution and presentation of domain results.

Key components include:

- `app/streamlit_app.py` — entry point;
- `app/ui/components.py` — shared UI components and semantic section headers;
- `app/ui/report.py` — Executive Report presentation;
- `app/ui/results/page.py` — Results page composition;
- `app/ui/results/dashboard.py` — Risk Indicator Dashboard;
- `app/ui/results/helpers.py` — deterministic rule-result helpers;
- `app/workflow/` — application-level workflow composition and execution wrapper.

The UI consumes `AssessmentWorkflowResult` and `RuleResult` objects rather than reimplementing business logic.

### Current Results hierarchy

The Results view is intentionally organized from the executive outcome toward deeper evidence:

```text
Executive Credit Assessment
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The hierarchy keeps the primary report concise while making deterministic evidence available on demand.

### Decision Path

The Results UI includes a graphical decision path:

```text
Financial Indicators
        ↓
Rule Engine Outcomes
        ↓
Monitoring Assessment
```

The visualization summarizes evaluated rules, triggered rules and non-evaluable rules together with the final assessment status. It consumes deterministic outputs and does not recalculate thresholds, severity or status.

### Risk Indicator Dashboard

`render_risk_indicator_dashboard()` provides the detailed rule-evidence surface. It includes:

- KPI counts for indicators, triggered rules, high/critical severity and non-evaluable rules;
- rule-outcome distribution;
- severity profile;
- filterable Rule Catalogue;
- filtering by status, severity and category;
- priority-oriented sorting;
- individual rule inspection.

The individual rule detail presents:

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

The audit area contains broader traceability information, including the Decision Path, credit data used, methodology and execution metadata. Detailed rule evidence remains centralized in the Risk Indicator Dashboard rather than duplicated across multiple panels.

---

## 6. Assessment Layer

`AssessmentService` owns the deterministic assessment stage:

```text
CreditPosition
      ↓
CreditPositionValidator
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

No LLM is involved in this path.

### Status calculation

The current status logic is:

| Rule outcome condition | Assessment |
|---|---|
| 2+ `TRIGGERED` | `CRITICAL` |
| Exactly 1 `TRIGGERED` | `ATTENTION` |
| 0 triggered and at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

The all-`NOT_EVALUABLE` case is intentionally conservative: the absence of evaluable evidence is not treated as equivalent to a normal assessment.

### Domain model

The domain model `Assessment` contains:

- `position_id`;
- `rule_results`;
- `findings`;
- `status`.

---

## 7. Rule Engine

Rules implement a common abstraction and are resolved through the rule registry.

```text
Rule.evaluate(position) → RuleResult
```

The current configured rule catalogue contains revenue, profitability, leverage and interest-coverage indicators.

### Rule outcomes

Each rule can produce:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

`NOT_EVALUABLE` is used when a rule cannot safely assess its indicator because the required domain data is unavailable or unsuitable. This state is distinct from `NOT_TRIGGERED`.

### Configuration

Rule parameters are externalized in:

```text
config/rules.yaml
```

Configuration includes rule identifiers, names, categories, trigger thresholds, severity and severity direction, with optional graduated severity thresholds.

### Discovery

The registry/discovery mechanism connects configured `rule_id` values to concrete implementations. The central assessment service therefore does not require a growing rule-specific dispatcher.

---

## 8. Analysis Layer

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

## 9. Reporting Layer

`ReportingAgent` converts `AssessmentAnalysis` into a `Report`.

Supported generators are:

```text
DeterministicReportGenerator
          OR
LLMReportGenerator
```

The report model contains the deterministic assessment status, executive summary, grouped findings and limitations.

For LLM-assisted reporting, the deterministic status remains application-controlled and is presented separately from generated prose.

---

## 10. LLM Architecture

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

The prompt builder receives deterministic findings and explicitly constrains the model to narrative generation. The current contract requires supplied material findings and numerical indicators to remain represented, prohibits unsupported causal explanations, controls category ordering and repetition, and prevents the model from generating the assessment status.

### Indicator grounding validation

`LLMReportGenerator` can run in strict indicator-grounding mode. Deterministic indicator values extracted from supplied findings must be represented in the generated narrative. Missing required values cause deterministic fallback.

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

The validation is deliberately narrow: it protects required numerical evidence but does not attempt full semantic verification of arbitrary natural language.

---

## 11. Reliability and Failure Handling

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

## 12. Execution Observability

`AssessmentWorkflowResult` exposes immutable execution information alongside the assessment, analysis and report.

The execution metadata includes:

- unique execution ID;
- UTC start timestamp;
- reporting mode;
- generator used;
- fallback state;
- classified reporting error category when applicable;
- assessment, analysis, reporting and total elapsed time.

The UI exposes this information in the audit area rather than mixing it into the primary credit judgement.

---

## 13. Domain Model

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

---

## 14. Repository Structure

```text
credit-assessment-system/
├── app/                         # Streamlit presentation layer
│   ├── streamlit_app.py
│   ├── ui/
│   │   ├── components.py
│   │   ├── report.py
│   │   └── results/
│   │       ├── page.py
│   │       ├── dashboard.py
│   │       └── helpers.py
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
│       ├── assessment_service.py
│       ├── assessment_status_calculator.py
│       └── position_validator.py
├── docs/
└── tests/
```

---

## 15. Extension Points

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

## 16. Architectural Boundary

```text
                 DETERMINISTIC CORE
                       │
                       ▼
              Input Validation
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
