# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment library with an optional AI-assisted reporting layer.

The architecture separates three concerns:

1. **Assessment** — deterministic evaluation of financial indicators and business rules.
2. **Analysis** — structured interpretation of the deterministic assessment.
3. **Reporting** — generation of a human-readable report, optionally using an LLM for narrative generation.

The core architectural boundary is:

> **The deterministic assessment is the source of truth. The LLM is an optional reporting component and has no decision authority.**

The repository is organized into a framework-independent Python library under `src/` and a thin Streamlit presentation layer under `app/`.

For the rationale behind these choices, see [`architecture-decisions.md`](architecture-decisions.md).

---

## 2. Architectural Principles

| Principle | Implementation |
|---|---|
| **Deterministic decision authority** | Rules and assessment status are computed without an LLM. |
| **Separation of concerns** | Assessment, analysis, and reporting are distinct workflow stages. |
| **Configuration-driven rules** | Thresholds and severity parameters are externalized in `config/rules.yaml`. |
| **Pluggable rules** | Rules are discovered and resolved through a registry using `rule_id`. |
| **Provider independence** | LLM providers are accessed through the `LLMClient` abstraction. |
| **Graceful degradation** | LLM reporting can fall back to deterministic report generation. |
| **Execution observability** | Workflow executions expose immutable provenance, fallback state, error classification, and phase timings. |
| **Immutable assessment state** | Core assessment, analysis, report, and execution metadata objects use immutable dataclasses where appropriate. |
| **UI/domain decoupling** | Streamlit is confined to `app/`; business logic lives in `src/`. |

---

## 3. System Architecture

### 3.1 High-Level Flow

```text
CreditPosition
      │
      ▼
AssessmentService
      │
      ├── RuleEngine
      │      └── RuleResult[]
      │
      ├── CommentEngine
      │      └── RuleFinding[]
      │
      └── AssessmentStatusCalculator
             │
             ▼
         Assessment
             │
             ▼
       AnalysisAgent
             │
             ▼
    AssessmentAnalysis
             │
             ▼
       ReportingAgent
          /       \
         /         \
Deterministic      LLM
Report Generator   Report Generator
         \         /
          \       /
           ▼     ▼
             Report

      + ExecutionMetadata
        ├── execution_id
        ├── started_at
        ├── reporting_mode
        ├── generator_used
        ├── fallback_used
        ├── error_category
        └── phase timings
```

The complete workflow is encapsulated by `AssessmentWorkflow` and exposed through `AssessmentOrchestrator`.

### 3.2 Dependency Direction

The intended dependency direction is:

```text
Presentation (`app/`)
        │
        ▼
Application / Orchestration
        │
        ▼
Domain Services / Agents
        │
        ▼
Rules / Domain Models
```

The core library does not depend on Streamlit.

Infrastructure-specific implementations, such as Gemini and Ollama clients, are hidden behind application-facing abstractions.

---

## 4. Component Architecture

### 4.1 Presentation Layer — `app/`

The Streamlit application is responsible for:

- collecting or selecting input data;
- selecting reporting mode;
- constructing the workflow through factory functions;
- executing the workflow;
- rendering the resulting domain objects and execution metadata.

The UI does not implement credit-risk business rules.

Key components include:

- `app/streamlit_app.py` — application entry point;
- `app/ui/` — presentation components;
- `app/workflow/assessment_workflow_factory.py` — workflow composition;
- `app/workflow/runner.py` — thin execution wrapper.

### 4.2 Orchestration Layer — `src/orchestration/`

`AssessmentOrchestrator` provides a simplified entry point for executing the assessment workflow and returning the final report.

Factories keep dependency construction outside the domain components.

### 4.3 Workflow Layer — `src/agents/workflow/`

`AssessmentWorkflow` coordinates the three processing stages:

```text
Assessment → Analysis → Reporting
```

The workflow also carries execution-level information such as execution identity, timing, reporting provenance, fallback state, and classified reporting errors through `ExecutionMetadata`.

### 4.4 Assessment Layer — `src/services/`

`AssessmentService` is the main deterministic application service. It coordinates:

1. rule evaluation;
2. comment generation for triggered rules;
3. aggregate assessment-status calculation.

It returns an `Assessment` containing the complete deterministic result.

---

## 5. Domain Model

The workflow communicates through explicit domain objects rather than passing loosely structured dictionaries between components.

| Model | Responsibility |
|---|---|
| `CreditPosition` | Input financial position to be assessed. |
| `RuleResult` | Result of evaluating one rule. |
| `Comment` | Human-readable explanation for a triggered rule. |
| `RuleFinding` | Structured pairing of a rule result and its comment. |
| `Assessment` | Complete deterministic assessment. |
| `AnalysisFinding` | Normalized finding used by downstream analysis/reporting. |
| `AssessmentAnalysis` | Structured representation of findings, risk factors, status, and limitations. |
| `Report` | Final user-facing deliverable. |
| `ExecutionMetadata` | Immutable provenance, fallback, error classification, and timing information for one workflow execution. |
| `AssessmentWorkflowResult` | Complete workflow output including assessment, analysis, report, provenance, and timing information. |

### 5.1 Status and Severity

`RuleStatus`:

- `TRIGGERED`
- `NOT_TRIGGERED`
- `NOT_EVALUABLE`

`RuleSeverity`:

- `LOW`
- `MEDIUM`
- `HIGH`

`AssessmentStatus`:

- `NORMAL`
- `ATTENTION`
- `CRITICAL`

`SeverityDirection` determines whether higher or lower values represent worse outcomes for a rule.

---

## 6. Rule Engine

The Rule Engine is the main deterministic decision component.

### 6.1 Rule Abstraction

Concrete rules extend the common `Rule` abstraction and implement:

```text
Rule.evaluate(position) → RuleResult
```

A rule is responsible for evaluating one specific business condition. The engine itself does not contain rule-specific business logic.

### 6.2 Rule Registry and Discovery

Rules are registered by `rule_id` and discovered through the rule discovery mechanism.

The registry maps configured rule identifiers to concrete rule implementations.

This means the central engine does not require a growing `if/elif` dispatcher for every rule.

### 6.3 Rule Configuration

Rule parameters are externalized in:

```text
config/rules.yaml
```

The configuration layer converts YAML entries into validated `RuleConfig` objects.

Typical parameters include:

- `rule_id`;
- `rule_name`;
- `category`;
- `threshold`;
- `severity`;
- `severity_direction`;
- optional severity thresholds.

### 6.4 Severity Policy

`SeverityPolicy` determines the resolved severity from a numeric value, severity direction, and configured thresholds.

This keeps severity interpretation separate from the concrete rule implementation.

---

## 7. Assessment Pipeline

### 7.1 Assessment Service

The first workflow stage is deterministic:

```text
CreditPosition
      ↓
RuleEngine
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

No LLM is involved in this stage.

### 7.2 Analysis Agent

`AnalysisAgent` converts an `Assessment` into an `AssessmentAnalysis`.

It organizes deterministic information into:

- key findings;
- risk factors;
- limitations;
- assessment status.

It does not perform a second credit assessment.

### 7.3 Reporting Agent

`ReportingAgent` converts `AssessmentAnalysis` into a `Report`.

The reporting strategy can be:

```text
Deterministic reporting
        OR
LLM-assisted reporting
```

Both paths consume the same structured analysis.

---

## 8. LLM Architecture

### 8.1 Provider Abstraction

LLM access is defined through `LLMClient` rather than directly through a provider SDK.

Current implementations include:

```text
LLMClient
   ├── GeminiClient
   ├── OllamaClient
   └── MockLLMClient
```

This allows the reporting layer to remain independent from the concrete provider.

### 8.2 Prompt Construction

The prompt builder receives deterministic findings and constructs a constrained reporting prompt.

The prompt explicitly establishes that:

- deterministic assessment is the source of truth;
- the LLM is only responsible for language generation;
- supplied numerical values must be preserved;
- unsupported facts must not be invented;
- the LLM cannot make or change a credit decision.

### 8.3 Fallback and Error Classification

When LLM reporting is unavailable or its output is rejected by validation, the workflow can use `DeterministicReportGenerator`.

The reporting agent classifies primary reporting failures into operational categories such as:

```text
RATE_LIMIT
SERVICE_UNAVAILABLE
CONNECTION_ERROR
AUTHENTICATION
AUTHORIZATION
MODEL_UNAVAILABLE
TIMEOUT
GENERATION_ERROR
```

The fallback changes the narrative generation path only; it does not change the underlying assessment.

If both the primary and fallback generators fail, the terminal error is propagated rather than silently masking the failure.

---

## 9. Execution Observability

Each successfully completed workflow execution can expose immutable `ExecutionMetadata` through `AssessmentWorkflowResult`.

The metadata captures:

- a unique `execution_id`;
- UTC `started_at` timestamp;
- selected `reporting_mode`;
- generator used (`PRIMARY`, `FALLBACK`, or unavailable after terminal failure);
- whether fallback was used;
- classified reporting `error_category`, when applicable;
- assessment, analysis, reporting, and total execution times.

Conceptually:

```text
Workflow Execution
        │
        ▼
ExecutionMetadata
        ├── Identity
        ├── Timestamp
        ├── Reporting provenance
        ├── Error classification
        └── Phase timings
```

The metadata is intended for traceability and operational diagnostics. It does not become part of the deterministic credit decision.

The Streamlit application exposes these fields through the **Execution & Audit Metadata** section of the Executive Report.

---

## 10. Repository Structure

```text
credit-assessment-system/
├── app/                         # Streamlit presentation layer
│   ├── streamlit_app.py
│   ├── config.py
│   ├── demo_scenarios.py
│   ├── ui/
│   └── workflow/
│
├── src/                         # Framework-independent application/domain library
│   ├── agents/                  # Analysis, reporting, workflow, agent abstraction
│   ├── comments/                # Rule comments and templates
│   ├── config/                  # Rule configuration loading
│   ├── engine/                  # Rule and finding execution
│   ├── llm/                     # LLM abstraction and provider implementations
│   ├── models/                  # Domain data structures
│   ├── orchestration/           # Workflow orchestration
│   ├── rules/                   # Rule catalog, discovery, registry
│   └── services/                # Assessment services
│
├── config/
│   └── rules.yaml               # Declarative rule configuration
│
├── docs/
│   ├── architecture.md          # System architecture
│   ├── architecture-decisions.md# Architectural decisions and rationale
│   ├── validation.md             # Validation and testing strategy
│   └── security-data-handling.md# Security and data-handling principles
│
└── tests/                       # Unit, integration and workflow tests
```

---

## 11. Extension Points

### 11.1 Adding a New Rule

A new rule requires:

1. a concrete `Rule` implementation;
2. a unique `rule_id` registration;
3. a corresponding configuration entry in `config/rules.yaml`.

The central Rule Engine does not need to be modified.

### 11.2 Adding a New LLM Provider

A new provider can implement the `LLMClient` interface and be injected into the reporting workflow.

The assessment engine remains unchanged.

### 11.3 Adding a New Report Generator

A new report generator can implement the reporting abstraction and consume the existing `AssessmentAnalysis`.

The deterministic assessment remains independent of the reporting implementation.

---

## 12. Architectural Boundary

The system deliberately separates **decision authority** from **language generation**:

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
```

The LLM is therefore an optional reporting dependency rather than a component of the credit decision itself.

For the rationale and trade-offs behind this architecture, see [`architecture-decisions.md`](architecture-decisions.md).
