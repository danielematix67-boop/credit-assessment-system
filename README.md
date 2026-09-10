# Credit Assessment System

> A production-oriented credit risk assessment prototype combining a deterministic Rule Engine, structural input validation, explainable assessment evidence, resilient LLM-assisted reporting, and execution-level observability.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** is a Python-based credit risk assessment application that evaluates a company's credit position through configurable deterministic rules and produces explainable assessment evidence and an executive report.

The architecture deliberately separates **credit decision-making from AI-generated communication**:

- structural input validation checks a `CreditPosition` before assessment;
- the deterministic Rule Engine evaluates indicators and determines rule outcomes;
- assessment services consolidate deterministic evidence into macro-area and final statuses;
- the Analysis Layer organizes deterministic findings;
- the Reporting Layer generates deterministic, Gemini or local Ollama narratives;
- LLM reporting is bounded by a grounding contract and can fall back to deterministic reporting;
- immutable Execution Metadata records reporting provenance, fallback state, errors and timings.

> **Core principle: the system decides; AI explains. The LLM has no authority over the credit judgement.**

---

## Architecture at a Glance

```text
Credit Position
      ↓
Structural Validation
      ↓
Deterministic Assessment
      ├── Customer Profile
      ├── Financial Analysis → R001–R007
      ├── Behavioural Analysis → B001–B004
      └── Debt Sustainability → DS001–DS003
                    ↓
             Final Assessment
                    ↓
             Deterministic Analysis
                    ↓
          Reporting / LLM Narrative
                    ↓
                  Report
                    ↓
           Execution Metadata
```

The deterministic core owns the assessment. The LLM receives already-produced evidence and can only transform that evidence into narrative.

---

## Key Features

### Structural Input Validation

`CreditPositionValidator` runs before financial rule evaluation and checks:

- valid `CreditPosition` type;
- non-empty `position_id`;
- numeric financial fields or `None`;
- rejection of booleans where numeric values are expected;
- rejection of `NaN` and positive/negative infinity.

`None` remains valid because missing information is a legitimate domain condition and can produce `NOT_EVALUABLE`. The validator intentionally does not impose business-specific sign constraints; those belong to individual rules.

### Deterministic Rule Engine

The Rule Engine:

- evaluates configurable credit indicators;
- returns structured `RuleResult` objects;
- supports `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE`;
- applies configurable severity and severity direction;
- remains independent from Streamlit presentation.

### Assessment Status

The financial assessment status is deterministic:

| Condition | Status |
|---|---|
| Two or more triggered rules | `CRITICAL` |
| Exactly one triggered rule | `ATTENTION` |
| No triggered rules + at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty rule-result set | `NORMAL` |

### Analyst-Oriented Case Assessment

The case layer organizes the assessment into Customer Profile, Financial Analysis, Behavioural Analysis, Debt Sustainability, Final Assessment and Executive Synthesis.

The final consolidation is deterministic:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 ATTENTION section        → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

Customer Profile is contextual: its ATTENTION status does not count toward the two-core-area escalation, while a CRITICAL profile can still make the final assessment CRITICAL.

### Explainable Results UI

The current Results experience is intentionally progressive rather than a long technical page:

```text
Executive Credit Assessment
          ↓
Final Assessment
          ↓
Risk Drivers
          ↓
Rule Engine Evidence
          ↓
Executive Narrative
          ↓
Detailed Analysis by Macro-area
```

The main screen emphasizes the decision and its principal drivers. Detailed tables, individual rule evidence, limitations and macro-area analysis are available on demand through compact expanders.

The UI is presentation-only: it does not recalculate thresholds, severity or assessment status.

### Risk Drivers

The Risk Drivers view ranks deterministic triggered indicators across macro-areas using normalized distance from the configured threshold. The chart is immediately visible; the full triggered-indicator table is available through **View triggered indicators**.

This ranking is descriptive and does not create a new risk score.

### Rule Engine Evidence

The Rule Engine Evidence view provides rule-outcome distribution, severity profile, a filterable rule catalogue and individual rule inspection. The catalogue and detailed rule view are closed by default so the executive flow remains compact.

### Executive Reporting

The primary report contains deterministic assessment status, executive narrative, material findings, data limitations and reporting provenance.

For AI-assisted modes, the deterministic status is displayed separately from generated prose. The LLM is never asked to determine the credit status.

---

## Rule Catalogue

Rules are defined in [`config/rules.yaml`](config/rules.yaml).

| Rule | Indicator |
|---|---|
| `R001` | Revenue growth deterioration |
| `R002` | Negative EBITDA |
| `R003` | EBITDA margin deterioration |
| `R004` | NFP / EBITDA leverage |
| `R005` | Interest expense to EBITDA |
| `R006` | EBITDA materially supported by finished goods inventory increase |
| `R007` | Interest coverage ratio |

Additional case-level indicator families include:

| Family | Scope |
|---|---|
| `B001–B004` | Behavioural risk indicators |
| `DS001–DS003` | Debt-service / cash-flow sustainability |
| `CP001–CP002` | Active EWS and previous restructuring flags |

Rule parameters are externalized from implementation and resolved through the rule registry.

---

## AI-Assisted Reporting

The reporting layer supports:

| Mode | Description |
|---|---|
| **Deterministic** | Template-based report from deterministic findings |
| **Gemini + Fallback** | Gemini narrative with deterministic fallback |
| **Ollama + Fallback** | Local LLM narrative with deterministic fallback |

The LLM prompt requires generated prose to remain grounded in supplied evidence. It must preserve material numerical values, represent supplied findings, avoid unsupported causes and avoid inventing information about sales volume, pricing, demand, costs, liquidity, cash flow, debt-service capacity or financial stability.

When strict indicator grounding is enabled, required deterministic indicator values must be present in the generated narrative. A grounding failure triggers deterministic fallback.

### Reliability

```text
Primary Generator
      ↓
 Success ─────────────→ Report
      │
    Failure
      ↓
Error Classification
      ↓
Deterministic Fallback
      ├── Success → Report
      └── Failure → Propagate Error
```

Failure of the optional AI path never changes the deterministic assessment.

---

## Execution Observability

Successful workflow executions expose immutable metadata including execution ID, UTC timestamp, reporting mode, generator used, fallback state, error category when applicable, and phase timings.

Observability describes execution provenance; it does not participate in the credit decision.

---

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── config.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   ├── workflow_view.py
│   │   ├── input_source.py
│   │   ├── assessment_configuration.py
│   │   └── results/
│   │       ├── page.py
│   │       ├── case_overview.py
│   │       ├── final_assessment.py
│   │       ├── risk_drivers.py
│   │       ├── dashboard.py
│   │       └── executive_synthesis.py
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

Provide the API key through the environment or Streamlit secrets:

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

The test suite covers deterministic rules, configuration, validation, services, analysis, reporting, LLM clients, grounding, fallback/error classification, workflow orchestration, execution metadata and integration behavior.

The CI quality gates are:

```text
Ruff
  ↓
Mypy
  ↓
Pytest + coverage
```

The supported CI matrix includes Python **3.13 and 3.14**, with a configured coverage gate of **95% for `src`**.

Run locally:

```bash
ruff check .
mypy src
pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — current architecture, case structure, deterministic boundaries and Results UI.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — architectural decisions and rationale.
- [`docs/validation.md`](docs/validation.md) — validation strategy, status semantics, LLM grounding, resilience and CI gates.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — trust boundaries, data minimization, LLM handling and secrets.

---

## Design Principles

- **Deterministic decision logic** — explicit rules own the credit judgement.
- **Structural input validation** — malformed positions are rejected before assessment.
- **Explicit data-availability semantics** — `NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.
- **Explainability by design** — quantitative evidence remains traceable.
- **Separation of concerns** — domain, assessment, reporting and UI remain distinct.
- **Configuration over hard-coding** — thresholds are externalized.
- **AI as a bounded reporting layer** — LLMs generate narrative, not decisions.
- **Grounded generation** — material findings and numerical indicators are protected by explicit contracts.
- **Resilience** — AI reporting can fall back deterministically.
- **Auditability** — execution provenance is recorded separately from decision data.
- **Professional evidence presentation** — technical evidence is available without overwhelming the executive view.

---

## Roadmap

- [x] Deterministic credit Rule Engine
- [x] Configurable rule thresholds
- [x] Graduated severity levels
- [x] Explainable rule findings
- [x] Assessment workflow orchestration
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` assessment handling
- [x] LLM-assisted reporting
- [x] Gemini and local Ollama integration
- [x] Deterministic LLM fallback
- [x] Streamlit assessment interface
- [x] Case-level macro-area assessment
- [x] Behavioural analysis indicators
- [x] Debt sustainability indicators
- [x] Customer profile risk flags
- [x] Final deterministic aggregation
- [x] Decision-path and risk-driver visualisations
- [x] Executive Results hierarchy
- [x] Filterable Rule Engine evidence
- [x] LLM narrative grounding and indicator validation
- [x] Execution observability and audit metadata
- [x] LLM error classification and failure-path testing
- [x] Automated CI validation on Python 3.13 and 3.14
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring and evaluation metrics
- [ ] Additional rule families and external data sources

---

## Current Baseline

The current repository baseline reflects the completed deterministic case structure, explicit input validation and `NOT_EVALUABLE` semantics, bounded AI reporting, expanded testing, and the streamlined analyst-oriented Results experience.

The deterministic Rule Engine and deterministic case aggregation remain the sole source of truth for credit decisions. LLM components remain optional and non-decisional.

---

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, explainability and applied AI**.
