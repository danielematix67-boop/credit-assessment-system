# Credit Assessment System

> A production-oriented credit risk assessment prototype combining a deterministic Rule Engine, explainable assessment evidence, resilient LLM-assisted reporting, and execution-level observability.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** is a Python-based credit risk assessment application designed to evaluate a company's financial position against a configurable set of deterministic credit rules and produce an explainable assessment.

The system deliberately separates **decision-making from AI-generated communication**:

- the **Rule Engine** evaluates the credit position and determines the assessment outcome;
- the **Analysis Layer** organizes the rule findings into structured evidence;
- the **Reporting Layer** generates a human-readable narrative using either deterministic templates, Google Gemini, or a local Ollama model;
- an automatic **fallback mechanism** ensures that an LLM failure does not prevent reporting from completing;
- **Execution Metadata** records provenance, generator selection, error classification, and workflow timings.

The project is designed as a technical prototype demonstrating how **Credit Risk, Python software engineering, configurable rule systems, explainability, LLM integration, resilience, and auditability** can be combined in a controlled architecture.

---

## Why this project?

Credit assessment systems need to be more than a final risk label. A useful system should make it possible to answer four questions:

1. **What is the assessment result?**
2. **Why was this result produced?**
3. **Which rules and quantitative values provide the evidence?**
4. **How was the result generated and communicated?**

This project addresses these requirements through an explicit separation between the **deterministic decision layer** and the **AI-assisted reporting layer**.

> **Key design principle:** the LLM has no authority over the credit decision. It is used only to transform already-produced assessment evidence into a narrative report.

---

## Key Features

### Deterministic Rule Engine

- Evaluates a `CreditPosition` against configurable credit indicators.
- Produces structured `RuleResult` objects for every rule.
- Supports `TRIGGERED`, `NOT_TRIGGERED`, and `NOT_EVALUABLE` outcomes.
- Supports graduated severity levels such as `LOW`, `MEDIUM`, and `HIGH`.
- Keeps business rules separate from the presentation layer.

### Configuration-driven rules

Rules and thresholds are defined declaratively in `config/rules.yaml`, allowing the rule set to evolve without embedding thresholds directly in the UI.

### Explainable assessment

The application exposes the evidence behind the assessment rather than showing only a final status. The results interface highlights:

- primary risk drivers linked to triggered rules;
- supporting findings;
- actual indicator values;
- rule thresholds;
- rule status and severity;
- reasons associated with individual findings.

### AI-assisted reporting

The reporting layer supports interchangeable generators:

- deterministic template-based reporting;
- Google Gemini;
- local Ollama models.

AI-generated reporting is therefore an **augmentation layer**, not the decision engine.

### Resilient LLM integration

If an LLM is unavailable because of a timeout, connection error, authentication problem, rate limit, missing model, or service outage, the system classifies the failure and can switch to deterministic reporting.

If both the primary generator and fallback fail, the terminal error is propagated rather than silently masked.

### Execution observability

Each successful workflow execution can expose immutable execution metadata including:

- unique execution ID;
- UTC start timestamp;
- reporting mode;
- generator ultimately used;
- fallback status;
- classified error category;
- assessment, analysis, reporting, and total execution times.

This provides execution-level provenance without making observability part of the credit decision.

### Streamlit application

The web interface is organized around a simple assessment flow:

**Credit Position → Assessment → Results**

The results page follows the hierarchy:

**RESULT → WHY → EVIDENCE → CREDIT DATA → WORKFLOW → DETAILS**

This makes the assessment easier to inspect and communicate to a human user.

### Automated testing and code quality

The repository includes automated tests covering the main domain components, rule engine, services, agents, orchestration, LLM clients, reporting fallback behavior, and workflow execution metadata, together with strict type checking and linting.

---

## System Architecture

The application follows a layered, agent-based architecture:

```text
                         CREDIT POSITION
                               │
                               ▼
                 ┌─────────────────────────┐
                 │     ASSESSMENT SERVICE  │
                 │                         │
                 │   Deterministic Rules  │
                 │       + Rule Engine     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │       ASSESSMENT        │
                 │                         │
                 │ Rule Results            │
                 │ Findings                │
                 │ Overall Status          │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │      ANALYSIS AGENT     │
                 │                         │
                 │ Structures assessment   │
                 │ evidence and findings   │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │     REPORTING AGENT     │
                 │                         │
                 │ Deterministic / Gemini │
                 │ / Ollama                │
                 │ + deterministic fallback│
                 └────────────┬────────────┘
                              │
                              ▼
                           REPORT
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   EXECUTION METADATA    │
                 │ ID · timestamp · mode    │
                 │ generator · errors      │
                 │ phase timings            │
                 └─────────────────────────┘
```

### Decision Layer vs Reporting Layer

The most important architectural boundary is:

```text
┌──────────────────────────────────┐
│          DECISION LAYER          │
│                                  │
│  CreditPosition                  │
│        ↓                         │
│  Rule Engine                     │
│        ↓                         │
│  Rule Results                    │
│        ↓                         │
│  Assessment Status               │
│                                  │
│  Deterministic / auditable       │
└──────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│         REPORTING LAYER          │
│                                  │
│  Structured findings             │
│        ↓                         │
│  Deterministic / Gemini / Ollama│
│        ↓                         │
│  Narrative Report                │
│                                  │
│  AI-assisted / non-decisional    │
└──────────────────────────────────┘
```

This separation limits the role of generative AI in a credit-risk context: the LLM receives assessment evidence that has already been produced by deterministic logic and does not determine the underlying credit status.

---

## Reliability & Failure Handling

The reporting path is explicitly designed around failure containment:

```text
                 PRIMARY GENERATOR
                        │
                 ┌──────┴──────┐
                 │             │
              SUCCESS        FAILURE
                 │             │
                 ▼             ▼
               REPORT     ERROR CLASSIFICATION
                               │
                               ▼
                    DETERMINISTIC FALLBACK
                               │
                         ┌─────┴─────┐
                         │           │
                      SUCCESS      FAILURE
                         │           │
                         ▼           ▼
                       REPORT    PROPAGATE ERROR
```

Typical failure categories include `RATE_LIMIT`, `SERVICE_UNAVAILABLE`, `CONNECTION_ERROR`, `AUTHENTICATION`, `AUTHORIZATION`, `MODEL_UNAVAILABLE`, `TIMEOUT`, and `GENERATION_ERROR`.

The underlying deterministic assessment is not dependent on the availability of Gemini or Ollama. This is an intentional architectural property rather than an accidental error-handling behavior.

---

## Observability & Auditability

Execution provenance is kept separate from the assessment decision. The workflow records immutable metadata after successful reporting, while generator diagnostics provide information about the reporting path.

The combination of **execution ID + timestamp + reporting mode + generator + fallback status + error category + phase timings** allows an analyst or developer to understand how a result was produced without exposing technical details in the primary assessment view.

The Streamlit interface exposes these details in a dedicated **Execution & Audit Metadata** section.

---

## Assessment Decision Flow

The end-to-end decision path is:

```text
1. Credit Data
       │
       ▼
2. Rule Evaluation
       │
       ├── TRIGGERED
       ├── NOT_TRIGGERED
       └── NOT_EVALUABLE
       │
       ▼
3. Rule Findings
       │
       ▼
4. Overall Assessment Status
       │
       ▼
5. Structured Analysis
       │
       ▼
6. Executive Report
       │
       ▼
7. Execution Provenance
```

The UI mirrors this flow so that a user can move from the final outcome back to the underlying quantitative evidence and execution details.

---

## Rule Engine

Rules are defined declaratively in [`config/rules.yaml`](config/rules.yaml).

Each rule can specify:

| Field | Description |
|---|---|
| `rule_id` | Unique rule identifier, e.g. `R001` |
| `rule_name` | Human-readable indicator name |
| `category` | Rule category |
| `threshold` | Base evaluation threshold |
| `severity` | Severity assigned to the rule |
| `severity_direction` | Whether lower or higher values represent deterioration |
| `severity_thresholds` | Optional graduated severity thresholds |

### Current rules

| Rule | Indicator |
|---|---|
| `R001` | Revenue growth deterioration |
| `R002` | Negative EBITDA |
| `R003` | EBITDA margin deterioration |
| `R004` | NFP / EBITDA leverage |
| `R005` | Interest expense to EBITDA |
| `R006` | EBITDA materially supported by finished goods inventory increase |
| `R007` | Interest coverage ratio |

The rule discovery mechanism automatically imports rule modules under `src/rules`, keeping the registry synchronized with the codebase.

The resulting `RuleResult` contains the information required for downstream assessment and explanation, including the rule identifier, category, status, value, threshold, severity, and optional reason.

---

## Explainability

Explainability is implemented as a first-class part of the assessment workflow.

For each assessed rule, the application can expose:

```text
Rule
 ├── Status
 ├── Severity
 ├── Category
 ├── Indicator
 ├── Actual Value
 ├── Threshold
 └── Reason
```

The results page prioritizes findings linked to **triggered rules** as the primary risk drivers, while retaining supporting findings and non-triggered/non-evaluable outcomes for context.

This allows the user to move from:

**Overall Result → Risk Drivers → Rule → Actual Value vs Threshold**

without relying on an opaque model score.

---

## AI-Assisted Reporting

The reporting layer supports three modes:

| Mode | Description | Availability |
|---|---|---|
| **Deterministic** | Template-based report generated from assessment findings | Always |
| **Gemini + Fallback** | Gemini-generated narrative with deterministic fallback | Requires API key |
| **Ollama + Fallback** | Local LLM narrative with deterministic fallback | Local execution |

The reporting agent records the generator ultimately used and can expose fallback diagnostics when an LLM request fails.

This makes the AI component replaceable and operationally safer: the core assessment remains available even when the generative service is unavailable.

---

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py          # Streamlit entry point
│   ├── config.py                 # Environment and secrets configuration
│   ├── demo_scenarios.py         # Pre-built demo credit positions
│   └── ui/                       # Application UI and presentation components
│
├── config/
│   └── rules.yaml                # Declarative rule definitions and thresholds
│
├── src/
│   ├── agents/
│   │   ├── analysis/             # Analysis agent
│   │   ├── reporting/            # Reporting agent and generators
│   │   ├── workflow/             # Workflow and factory
│   │   └── base/                 # Agent abstraction
│   ├── comments/                 # Finding/comment generation
│   ├── config/                   # Rule configuration loading
│   ├── engine/                   # Rule and finding engines
│   ├── llm/                      # Gemini, Ollama and mock clients
│   ├── models/                   # Domain models
│   ├── orchestration/            # Orchestrator and factory
│   ├── rules/                    # Credit risk rule implementations
│   └── services/                 # Assessment and status services
│
├── tests/                        # Unit and integration tests
└── requirements.txt
```

---

## Example

A simplified assessment can be represented as:

```text
Credit Position
      │
      ├── Revenue Growth       → Rule R001
      ├── EBITDA               → Rule R002
      ├── EBITDA Margin        → Rule R003
      ├── NFP / EBITDA         → Rule R004
      └── Interest Coverage    → Rule R007

                    ↓

              Rule Results
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Triggered   Not Triggered  N/E
        │
        ▼
   Risk Drivers
        │
        ▼
 Assessment Status
        │
        ▼
 Executive Report
```

The actual thresholds are controlled by `config/rules.yaml` rather than by the UI.

---

## Installation

### Requirements

- Python 3.13+
- Git
- Optional: Ollama for local LLM reporting

```bash
git clone <repository-url>
cd credit-assessment-system
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\\Scripts\\activate       # Windows
pip install -r requirements.txt
```

---

## Configuration

### Gemini

Provide the API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key"
```

Or through Streamlit secrets:

```toml
GEMINI_API_KEY = "your-api-key"
```

### Ollama

For local execution:

```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen3:0.6b"
```

Or through Streamlit secrets:

```toml
[ollama]
host = "http://localhost:11434"
model = "qwen3:0.6b"
```

Ollama is only exposed when the application is running locally.

### Rule configuration

Business rules and thresholds can be modified in:

```text
config/rules.yaml
```

This keeps the rule definition separate from application presentation code.

---

## Usage

### Run the web application

```bash
streamlit run app/streamlit_app.py
```

The application allows the user to:

1. Select or provide a credit position.
2. Choose the reporting mode.
3. Execute the assessment workflow.
4. Inspect the overall result.
5. Review the primary risk drivers and rule evidence.
6. Inspect the assessed credit data and workflow trace.
7. Read the executive report and its generation provenance.

---

## Testing & Code Quality

The test suite covers the main components of the application, including:

- individual credit rules;
- Rule Engine behavior;
- services and status calculation;
- analysis and reporting agents;
- orchestration;
- LLM clients;
- reporting fallback and error-classification paths;
- terminal reporting failures;
- execution metadata and workflow propagation.

The CI pipeline runs linting, strict type checking, and the test suite with a coverage threshold.

Run locally with:

```bash
pytest
pytest --cov=src
mypy src
ruff check .
```

---

## Documentation

The repository includes dedicated technical documentation:

- [`Architecture`](docs/architecture.md) — system structure and component responsibilities.
- [`Architecture Decisions`](docs/architecture-decisions.md) — key architectural decisions and rationale.
- [`Validation`](docs/validation.md) — validation strategy, invariants, fallback behavior, and CI gates.
- [`Security & Data Handling`](docs/security-data-handling.md) — trust boundaries, data minimization, LLM handling, secrets, logging, and production considerations.

---

## Tech Stack

| Area | Technology |
|---|---|
| Language | Python 3.13+ |
| Application UI | Streamlit |
| Rule configuration | YAML / PyYAML |
| Cloud LLM | Google Gemini / `google-genai` |
| Local LLM | Ollama |
| Testing | pytest / pytest-cov |
| Type checking | mypy |
| Linting | ruff |

---

## Design Principles

The project follows a few principles that are particularly relevant to credit-risk applications:

- **Deterministic decision logic** — the credit assessment is based on explicit rules rather than an opaque generative model.
- **Explainability by design** — rule outcomes, thresholds, values and findings are exposed to the user.
- **Separation of concerns** — domain logic, orchestration, LLM integration, observability, and UI presentation are kept in distinct layers.
- **Configuration over hard-coding** — rule thresholds are maintained declaratively.
- **Resilience** — LLM failures do not invalidate the underlying deterministic assessment.
- **Auditability** — execution metadata provides provenance and timing information for successful workflow executions.
- **Testability** — the core components can be tested independently from the Streamlit interface.
- **Replaceable AI layer** — Gemini, Ollama and deterministic reporting share the same reporting role.

---

## Roadmap

- [x] Deterministic credit Rule Engine
- [x] Configurable rule thresholds
- [x] Graduated severity levels
- [x] Explainable rule findings
- [x] Assessment workflow orchestration
- [x] LLM-assisted reporting
- [x] Local Ollama integration
- [x] Deterministic LLM fallback
- [x] Streamlit assessment interface
- [x] Results evidence and risk-driver visualization
- [x] Execution observability and audit metadata
- [x] LLM error classification and failure-path testing
- [ ] Persistent assessment history
- [ ] Expanded monitoring and evaluation metrics
- [ ] Additional rule families and data sources

---

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, and applied AI**.

---
