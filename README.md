# Credit Assessment System

> A production-oriented credit risk assessment prototype combining a deterministic Rule Engine, explainable assessment evidence, resilient LLM-assisted reporting, and execution-level observability.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** is a Python-based credit risk assessment application that evaluates a company's financial position against a configurable set of deterministic credit rules and produces an explainable assessment and Executive Report.

The architecture deliberately separates **decision-making from AI-generated communication**:

- the **Rule Engine** evaluates financial indicators and determines rule outcomes and assessment status;
- the **Analysis Layer** organizes deterministic findings into structured evidence;
- the **Reporting Layer** produces the Executive Report using deterministic templates, Google Gemini, or a local Ollama model;
- LLM reporting is constrained to narrative generation and can fall back to deterministic reporting;
- **Execution Metadata** records reporting provenance, fallback state, error classification, and workflow timings.

> **Core principle:** the system decides; AI explains. The LLM has no authority over the credit judgement.

---

## Key Features

### Deterministic Rule Engine

- Evaluates a `CreditPosition` against configurable indicators.
- Produces structured `RuleResult` objects.
- Supports `TRIGGERED`, `NOT_TRIGGERED`, and `NOT_EVALUABLE` outcomes.
- Supports configurable severity and severity direction.
- Keeps business rules independent from the Streamlit UI.

### Explainable assessment

The results interface exposes the evidence behind the judgement, including:

- overall assessment status;
- actual indicator values;
- configured thresholds;
- rule status and severity;
- rule categories and rationale;
- a graphical path from financial indicators to Rule Engine outcomes and final assessment.

### Professional Results UI

The Streamlit Results view is organized around a clear operator-oriented hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment Overview
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The interface combines a concise executive result with progressively deeper deterministic evidence:

- **Executive Credit Assessment** — primary outcome and narrative report;
- **Assessment Overview** — compact KPIs and high-level assessment context;
- **Decision Path** — visual explanation of how financial indicators feed deterministic rule outcomes and the final monitoring assessment;
- **Risk Indicator Dashboard** — rule-outcome and severity distributions, filterable rule catalogue and priority-oriented inspection;
- **Rule Detail** — individual rule card showing indicator, observed value, configured threshold, status, severity, direction, category and rationale;
- **Audit Trail & Methodology** — credit data used, methodology, workflow path and execution metadata.

All visual evidence is presentation-only: the UI consumes deterministic `RuleResult` and assessment objects and does not recalculate thresholds, severity or assessment status.

This makes the application suitable for demonstrating not only *what* the system decided, but *how* the deterministic assessment mechanism produced the decision.

### Executive Report

The primary output is the **Executive Credit Assessment**. It contains:

- deterministic assessment status;
- executive conclusion;
- key risk drivers;
- data limitations;
- report-generation provenance.

For AI-assisted modes, the deterministic status is displayed separately from the generated narrative. The LLM is not asked to determine the status.

### AI-assisted reporting

The reporting layer supports:

| Mode | Description |
|---|---|
| **Deterministic** | Template-based report generated from deterministic findings |
| **Gemini + Fallback** | Gemini narrative with deterministic fallback |
| **Ollama + Fallback** | Local LLM narrative with deterministic fallback |

The LLM prompt requires the narrative to remain grounded in supplied findings. Material numerical indicators must be preserved, findings must not be omitted, unsupported causes must not be invented, and the narrative should avoid repeated indicators or category headings.

When strict indicator grounding is enabled, the generator validates that supplied indicator values are represented in the response. If validation fails, the deterministic report generator is used instead.

### Resilient LLM integration

Provider failures such as timeouts, connection errors, authentication problems, rate limits, unavailable models, or service outages are classified and can activate deterministic fallback.

If both the primary and fallback generators fail, the terminal error is propagated rather than silently converted into a successful report.

### Execution observability

Successful workflow executions expose immutable metadata including:

- execution ID;
- UTC start timestamp;
- reporting mode;
- generator used;
- fallback state;
- error category when applicable;
- assessment, analysis, reporting and total execution times.

Observability describes the execution path; it does not participate in the credit decision.

---

## System Architecture

```text
Credit Position
      │
      ▼
Deterministic Assessment
      │
      ├── Rule Engine
      │      └── RuleResult[]
      │
      ├── Findings / comments
      │
      └── Assessment Status
              │
              ▼
       AssessmentAnalysis
              │
              ▼
        Reporting Layer
          /          \\
         /            \\
 Deterministic       LLM
    Report           Narrative
         \\            /
          \\          /
              Report
                 │
                 ▼
        Execution Metadata
```

The most important architectural boundary is:

```text
DECISION LAYER                         REPORTING LAYER
──────────────────                    ──────────────────
CreditPosition                        Structured findings
      ↓                                      ↓
Rule Engine                          Deterministic / LLM
      ↓                                      ↓
Rule Results                              Report
      ↓
Assessment Status

Deterministic / auditable             AI-assisted / non-decisional
```

The LLM consumes already-produced assessment evidence. It cannot change the underlying `Assessment` or its status.

---

## Assessment Decision Flow

```text
1. Credit Data
       ↓
2. Financial Indicators
       ↓
3. Rule Evaluation
       ├── TRIGGERED
       ├── NOT_TRIGGERED
       └── NOT_EVALUABLE
       ↓
4. Rule Findings
       ↓
5. Assessment Status
       ↓
6. Structured Analysis
       ↓
7. Executive Report
       ↓
8. Execution Provenance
```

The Streamlit interface mirrors this flow through a compact graphical **Decision Path**. The visualization highlights the deterministic boundary between financial indicators, rule outcomes and the final monitoring assessment.

---

## Rule Engine

Rules are defined in [`config/rules.yaml`](config/rules.yaml). The current rule catalogue contains seven indicators:

| Rule | Indicator |
|---|---|
| `R001` | Revenue growth deterioration |
| `R002` | Negative EBITDA |
| `R003` | EBITDA margin deterioration |
| `R004` | NFP / EBITDA leverage |
| `R005` | Interest expense to EBITDA |
| `R006` | EBITDA materially supported by finished goods inventory increase |
| `R007` | Interest coverage ratio |

Rule configuration separates business parameters from Python implementation. Rule discovery and the registry keep the central engine independent from individual concrete rules.

A `RuleResult` provides the downstream evidence needed for assessment and explanation, including rule identifier, category, status, value, threshold, severity and reason.

---

## Explainability

For each evaluated rule the application can expose:

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

The main operator path is:

**Overall Result → Assessment Overview → Risk Indicator Dashboard → Rule Detail**

The Decision Path provides the higher-level mechanism, while the Risk Indicator Dashboard provides detailed rule evidence. The UI does not reconstruct or duplicate rule calculations.

---

## AI Reporting Grounding

The reporting prompt establishes a strict boundary between deterministic evidence and generated language.

The narrative must:

- represent all supplied material findings;
- preserve supplied numerical values and units;
- avoid rounding, recalculation or conversion;
- avoid unsupported causal explanations;
- avoid inventing information about sales volume, pricing, demand, costs, liquidity, cash flow, debt service capacity or financial stability unless supplied;
- preserve the order of material categories;
- mention each material indicator value once;
- avoid category headings, bullets and duplicated conclusions;
- end after the final material finding.

The deterministic assessment status is constructed by application logic and is displayed as a separate status line, for example:

```text
Assessment Status: Critical

<LLM-generated narrative>
```

This prevents the generated prose from becoming the source of truth for the credit classification.

---

## Reliability & Failure Handling

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

The fallback affects report generation only. It never changes the deterministic assessment.

---

## Streamlit Application

The interface is organized around:

**Credit Position → Assessment → Results**

The Results page follows the operator-oriented hierarchy:

**Executive Report → Assessment Overview → Risk Indicator Dashboard → Audit Trail**

The main result sections are:

1. **Executive Credit Assessment** — primary output and narrative.
2. **Assessment Overview** — concise assessment KPIs and context.
3. **Risk Indicator Dashboard** — detailed deterministic rule evidence, distributions and filterable catalogue.
4. **Audit Trail & Methodology** — decision path, credit data, methodology and execution metadata.

The detailed dashboard supports filtering by rule status, severity and category, priority-oriented sorting, and inspection of an individual rule through its indicator, actual value, configured threshold and rationale.

The UI deliberately avoids duplicating legacy evidence views. The Risk Indicator Dashboard is the single detailed rule-evidence surface, while the Audit Trail contains the broader workflow and traceability information.

---

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── config.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   ├── charts.py
│   │   ├── report.py
│   │   ├── results.py
│   │   ├── workflow_view.py
│   │   └── ...
│   └── workflow/
│
├── config/
│   └── rules.yaml
│
├── src/
│   ├── agents/
│   │   ├── analysis/
│   │   ├── reporting/
│   │   └── workflow/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   ├── orchestration/
│   ├── rules/
│   └── services/
│
├── docs/
├── tests/
└── requirements.txt
```

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
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the application

```bash
streamlit run app/streamlit_app.py
```

### Gemini

Set the API key through the environment or Streamlit secrets:

```bash
export GEMINI_API_KEY="your-api-key"
```

### Ollama

For local reporting:

```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen3:0.6b"
```

---

## Testing & Code Quality

The test suite covers rules, configuration, Rule Engine behavior, services, analysis, reporting, LLM clients, fallback/error classification, workflow orchestration, execution metadata and integration behavior.

The dedicated LLM reporting tests also cover the narrative contract, including indicator grounding, ordering, non-repetition, deterministic status protection and fallback when required indicator values are missing.

The CI workflow runs on Python **3.13 and 3.14** and enforces:

```text
Ruff
  ↓
Mypy
  ↓
Pytest + coverage
```

The configured coverage gate is **95% for `src`**.

Run locally with:

```bash
ruff check .
mypy src
pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture, component responsibilities and current Results UI structure.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — architectural decisions and rationale.
- [`docs/validation.md`](docs/validation.md) — validation strategy, LLM grounding contract, fallback behavior and CI gates.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — trust boundaries, data minimization, LLM handling and secrets.

---

## Design Principles

- **Deterministic decision logic** — explicit rules own the credit judgement.
- **Explainability by design** — quantitative evidence is visible and traceable.
- **Separation of concerns** — assessment, analysis, reporting and UI remain distinct.
- **Configuration over hard-coding** — thresholds are externalized.
- **AI as a bounded reporting layer** — LLMs generate narrative, not decisions.
- **Grounded generation** — material findings and numerical indicators are protected by prompt and validation contracts.
- **Resilience** — LLM failures can fall back to deterministic reporting.
- **Auditability** — execution metadata records reporting provenance and timings.
- **Testability** — deterministic core logic is independently testable.
- **Professional evidence presentation** — the UI explains the deterministic mechanism without reproducing business logic.

---

## Roadmap

- [x] Deterministic credit Rule Engine
- [x] Configurable rule thresholds
- [x] Graduated severity levels
- [x] Explainable rule findings
- [x] Assessment workflow orchestration
- [x] LLM-assisted reporting
- [x] Gemini and local Ollama integration
- [x] Deterministic LLM fallback
- [x] Streamlit assessment interface
- [x] Decision-path and risk-indicator visualisations
- [x] Executive Report hierarchy
- [x] Filterable rule catalogue and individual rule evidence
- [x] LLM narrative grounding and indicator validation
- [x] Execution observability and audit metadata
- [x] LLM error classification and failure-path testing
- [ ] Persistent assessment history
- [ ] Expanded monitoring and evaluation metrics
- [ ] Additional rule families and data sources

---

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, explainability and applied AI**.
