# Credit Assessment System

> A production-oriented credit risk assessment prototype combining a deterministic Rule Engine, structural input validation, explainable assessment evidence, resilient LLM-assisted reporting, and execution-level observability.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** is a Python-based credit risk assessment application that evaluates a company's financial position against a configurable set of deterministic credit rules and produces an explainable assessment and Executive Report.

The architecture deliberately separates **decision-making from AI-generated communication**:

- the **input validation layer** checks the structural integrity of a `CreditPosition` before assessment;
- the **Rule Engine** evaluates financial indicators and determines rule outcomes and assessment status;
- the **Analysis Layer** organizes deterministic findings into structured evidence;
- the **Reporting Layer** produces the Executive Report using deterministic templates, Google Gemini, or a local Ollama model;
- LLM reporting is constrained to narrative generation and can fall back to deterministic reporting;
- **Execution Metadata** records reporting provenance, fallback state, error classification, and workflow timings.

> **Core principle:** the system decides; AI explains. The LLM has no authority over the credit judgement.

---

## Key Features

### Structural Input Validation

Every assessment validates the incoming `CreditPosition` before rule evaluation.

The validator checks that:

- the input is a valid `CreditPosition` instance;
- `position_id` is non-empty;
- financial fields are numeric or `None`;
- boolean values are rejected where numeric values are expected;
- `NaN`, positive infinity and negative infinity are rejected.

`None` remains valid because missing financial information is a legitimate input condition and is handled by the rule layer through `NOT_EVALUABLE` where applicable.

The validator intentionally performs **structural validation only**. It does not impose arbitrary business-sign constraints on financial values; business semantics remain owned by the individual rules.

### Deterministic Rule Engine

- Evaluates a `CreditPosition` against configurable indicators.
- Produces structured `RuleResult` objects.
- Supports `TRIGGERED`, `NOT_TRIGGERED`, and `NOT_EVALUABLE` outcomes.
- Supports configurable severity and severity direction.
- Keeps business rules independent from the Streamlit UI.

### Assessment Status

The overall status is calculated deterministically from rule outcomes:

| Condition | Assessment Status |
|---|---|
| Two or more triggered rules | `CRITICAL` |
| Exactly one triggered rule | `ATTENTION` |
| No triggered rules and at least one evaluable rule | `NORMAL` |
| All rules are `NOT_EVALUABLE` | `ATTENTION` |
| No rule results | `NORMAL` |

The explicit all-`NOT_EVALUABLE` case avoids treating **absence of evaluable evidence** as equivalent to a normal credit assessment.

### Explainable Assessment

The Results interface exposes the evidence behind the judgement, including:

- overall assessment status;
- actual indicator values;
- configured thresholds;
- rule status and severity;
- rule categories and rationale;
- a graphical path from financial indicators to Rule Engine outcomes and final assessment.

### Professional Results UI

The current Results view is organized around a clear operator-oriented hierarchy:

```text
Executive Credit Assessment
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The interface combines a concise executive result with progressively deeper deterministic evidence:

- **Executive Credit Assessment** — primary outcome and narrative report;
- **Risk Indicator Dashboard** — rule-outcome and severity distributions, filterable rule catalogue and priority-oriented inspection;
- **Rule Detail** — individual rule card showing indicator, observed value, configured threshold, status, severity, direction, category and rationale;
- **Audit Trail & Methodology** — decision path, credit data used, methodology, workflow path and execution metadata.

The dashboard is the single detailed rule-evidence surface. The UI does not recalculate thresholds, severity or assessment status.

### Decision Path

The Results UI provides a graphical explanation of the deterministic decision mechanism:

```text
Financial Indicators
        ↓
Rule Engine Outcomes
        ↓
Monitoring Assessment
```

The visualization summarizes evaluated rules, triggered rules, non-evaluable rules and the final assessment status. It consumes deterministic outputs and is presentation-only.

### Risk Indicator Dashboard

The dashboard provides:

- indicator/rule count KPIs;
- triggered-rule count;
- high/critical severity count;
- `NOT_EVALUABLE` count;
- rule-outcome distribution;
- severity profile;
- filterable Rule Catalogue;
- filtering by status, severity and category;
- priority-oriented sorting;
- individual rule inspection.

### Executive Report

The primary output is the **Executive Credit Assessment**. It contains:

- deterministic assessment status;
- executive conclusion;
- key risk drivers;
- data limitations;
- report-generation provenance.

For AI-assisted modes, the deterministic status is displayed separately from the generated narrative. The LLM is not asked to determine the status.

### AI-Assisted Reporting

The reporting layer supports:

| Mode | Description |
|---|---|
| **Deterministic** | Template-based report generated from deterministic findings |
| **Gemini + Fallback** | Gemini narrative with deterministic fallback |
| **Ollama + Fallback** | Local LLM narrative with deterministic fallback |

The LLM prompt requires the narrative to remain grounded in supplied findings. Material numerical indicators must be preserved, findings must not be omitted, unsupported causes must not be invented, and the narrative should avoid repeated indicators or category headings.

When strict indicator grounding is enabled, the generator validates that supplied indicator values are represented in the response. If validation fails, the deterministic report generator is used instead.

### Resilient LLM Integration

Provider failures such as timeouts, connection errors, authentication problems, rate limits, unavailable models, or service outages are classified and can activate deterministic fallback.

If both the primary and fallback generators fail, the terminal error is propagated rather than silently converted into a successful report.

### Execution Observability

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
Input Validation
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
Input Validator                       Deterministic / LLM
      ↓                                      ↓
Rule Engine                              Report
      ↓
Rule Results
      ↓
Assessment Status

Deterministic / auditable             AI-assisted / non-decisional
```

The LLM consumes already-produced assessment evidence. It cannot change the underlying `Assessment` or its status.

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

## Assessment and `NOT_EVALUABLE` Handling

The assessment pipeline distinguishes between a rule that did not trigger and a rule that could not be evaluated.

```text
TRIGGERED       → contributes to risk status
NOT_TRIGGERED   → evaluated and no trigger detected
NOT_EVALUABLE   → insufficient/invalid domain data for that rule
```

The status calculator therefore applies the following precedence:

```text
2+ TRIGGERED
      ↓
   CRITICAL

1 TRIGGERED
      ↓
  ATTENTION

0 TRIGGERED + ALL NOT_EVALUABLE
      ↓
  ATTENTION

0 TRIGGERED + at least one evaluable rule
      ↓
   NORMAL
```

This prevents a data-availability problem from being silently interpreted as evidence of normal credit quality.

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

**Overall Result → Risk Indicator Dashboard → Rule Detail → Audit Trail**

The Decision Path provides the higher-level mechanism, while the Risk Indicator Dashboard provides detailed rule evidence. The UI does not reconstruct or duplicate rule calculations.

---

## AI Reporting Grounding

The reporting prompt establishes a strict boundary between deterministic evidence and generated language.

The narrative must:

- represent all supplied material findings;
- preserve supplied numerical values and units exactly;
- avoid rounding, recalculation or conversion;
- avoid unsupported causal explanations;
- avoid inventing information about sales volume, pricing, demand, costs, liquidity, cash flow, debt service capacity or financial stability unless supplied;
- preserve the order of material categories;
- mention each material indicator value once;
- avoid category headings, bullets and duplicated conclusions;
- end after the final material finding.

The deterministic assessment status is constructed by application logic and is displayed as a separate status line. The generated prose is never the source of truth for the credit classification.

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

The current Results page follows:

**Executive Credit Assessment → Risk Indicator Dashboard → Audit Trail & Methodology**

The main result sections are:

1. **Executive Credit Assessment** — primary output and narrative.
2. **Risk Indicator Dashboard** — detailed deterministic rule evidence, distributions and filterable catalogue.
3. **Audit Trail & Methodology** — decision path, credit data, methodology and execution metadata.

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
│   │   ├── components.py
│   │   ├── report.py
│   │   ├── results/
│   │   │   ├── page.py
│   │   │   ├── dashboard.py
│   │   │   └── helpers.py
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
│       ├── assessment_service.py
│       ├── assessment_status_calculator.py
│       └── position_validator.py
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

The test suite covers rules, configuration, Rule Engine behavior, input validation, services, analysis, reporting, LLM clients, fallback/error classification, workflow orchestration, execution metadata and integration behavior.

The validation layer is explicitly tested for malformed position IDs, non-numeric values, booleans in numeric fields, and non-finite values such as `NaN` and infinities.

The assessment-status tests also protect the distinction between `NOT_EVALUABLE` and a normal assessment, including the all-`NOT_EVALUABLE` case.

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

- [`docs/architecture.md`](docs/architecture.md) — system architecture, component responsibilities, input validation and current Results UI structure.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — architectural decisions and rationale.
- [`docs/validation.md`](docs/validation.md) — validation strategy, structural input validation, `NOT_EVALUABLE` semantics, LLM grounding, fallback behavior and CI gates.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — trust boundaries, data minimization, LLM handling and secrets.

---

## Design Principles

- **Deterministic decision logic** — explicit rules own the credit judgement.
- **Structural input validation** — malformed positions are rejected before assessment.
- **Explicit data-availability semantics** — `NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.
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
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` assessment handling
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
- [x] Automated CI validation on Python 3.13 and 3.14
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring and evaluation metrics
- [ ] Additional rule families and data sources

---

## Current Baseline

The repository's current validated baseline is preserved by the **`v0.2.0`** release, which consolidates the improved Results UI, structural input validation, explicit `NOT_EVALUABLE` handling, expanded tests and CI validation.

The deterministic Rule Engine remains the sole source of truth for credit assessment decisions. LLM components remain restricted to analysis and natural-language reporting.

---

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, explainability and applied AI**.
