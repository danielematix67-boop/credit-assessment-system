# Credit Assessment System

> A production-oriented credit risk assessment prototype combining a deterministic Rule Engine, explainable assessment evidence, and LLM-assisted narrative reporting.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** is a Python-based credit risk assessment application designed to evaluate a company's financial position against a configurable set of deterministic credit rules and produce an explainable assessment.

The system deliberately separates **decision-making from AI-generated communication**:

- the **Rule Engine** evaluates the credit position and determines the assessment outcome;
- the **Analysis Layer** organizes the rule findings into structured evidence;
- the **Reporting Layer** generates a human-readable narrative using either deterministic templates, Google Gemini, or a local Ollama model;
- an automatic **fallback mechanism** ensures that an LLM failure does not prevent the assessment workflow from completing.

The project is designed as a technical prototype demonstrating how **Credit Risk, Python software engineering, configurable rule systems, explainability, and LLM integration** can be combined in a controlled architecture.

---

## Why this project?

Credit assessment systems need to be more than a final risk label. A useful system should make it possible to answer four questions:

1. **What is the assessment result?**
2. **Why was this result produced?**
3. **Which rules and quantitative values provide the evidence?**
4. **How can the result be communicated clearly to a human analyst?**

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

If an LLM is unavailable because of a timeout, connection error, authentication problem, rate limit, missing model, or service outage, the system automatically falls back to deterministic reporting.

### Streamlit application

The web interface is organized around a simple assessment flow:

**Credit Position → Assessment → Results**

The results page follows the hierarchy:

**RESULT → WHY → EVIDENCE → CREDIT DATA → WORKFLOW → DETAILS**

This makes the assessment easier to inspect and communicate to a human user.

### Automated testing and code quality

The repository includes automated tests covering the main domain components, rule engine, services, agents, orchestration, LLM clients, and integration flows, together with static type checking and linting.

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
```

The UI mirrors this flow so that a user can move from the final outcome back to the underlying quantitative evidence.

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
# .venv\Scripts\activate       # Windows
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

### Run programmatically

```python
from src.orchestration.orchestrator_factory import create_default_orchestrator
from src.models.position import CreditPosition

orchestrator = create_default_orchestrator()

position = CreditPosition(
    position_id="ACME-2025",
    revenue=1_000_000,
    ebitda=80_000,
    ebitda_margin=0.08,
    nfp_to_ebitda=6.2,
    # ... other financial fields
)

report = orchestrator.run(position)
print(report)
```

---

## Testing & Code Quality

The test suite covers the main components of the application, including:

- individual credit rules;
- Rule Engine behavior;
- services and status calculation;
- analysis and reporting agents;
- orchestration;
- LLM clients;
- integration workflows.

Run the tests with:

```bash
pytest
```

Coverage:

```bash
pytest --cov=src
```

Static type checking:

```bash
mypy src
```

Linting:

```bash
ruff check .
```

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
- **Separation of concerns** — domain logic, orchestration, LLM integration and UI presentation are kept in distinct layers.
- **Configuration over hard-coding** — rule thresholds are maintained declaratively.
- **Resilience** — LLM failures do not invalidate the underlying assessment workflow.
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
- [ ] Persistent assessment history
- [ ] Expanded monitoring and evaluation metrics
- [ ] Additional rule families and data sources

---

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, and applied AI**.

---
