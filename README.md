# Credit Assessment System

> A production-oriented credit-risk assessment prototype combining deterministic rule-based decisioning, structural validation, explainable evidence, multi-domain case assessment, resilient LLM-assisted reporting and execution observability.

[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** is a Python application that evaluates a synthetic credit position through deterministic, configurable rules and presents the resulting evidence through an analyst-oriented Streamlit interface.

The architecture deliberately separates **credit decision-making from AI-generated communication**:

- `CreditPositionValidator` validates structural input before assessment;
- deterministic rule engines evaluate the configured indicators;
- domain services consolidate evidence into macro-area sections;
- `FinalAssessmentService` performs deterministic cross-area aggregation;
- analysis components organize deterministic findings;
- reporting supports deterministic, Gemini and local Ollama narratives;
- LLM output is bounded by an explicit grounding contract and deterministic fallback;
- immutable execution metadata records reporting provenance and timings.

> **Core principle: the system decides; AI explains. The LLM has no authority over the credit judgement.**

## Architecture at a Glance

```text
Credit Position
      ↓
Structural Validation
      ↓
Deterministic Case Assessment
      ├── Customer Profile → CP001–CP002
      ├── Financial Analysis → R001–R007
      ├── Behavioural Analysis → B001–B004
      └── Debt Sustainability → DS001–DS003
                    ↓
             Final Assessment
                    ↓
          Deterministic Analysis
                    ↓
        Reporting / optional LLM
                    ↓
                  Report
                    ↓
           Execution Metadata
```

The deterministic core is the single source of truth for structured credit outcomes. The LLM only transforms supplied evidence into narrative text.

## Assessment Model

The application uses four deterministic assessment domains:

| Domain | Rule family | Purpose |
|---|---|---|
| Customer Profile | `CP001–CP002` | Active EWS and previous restructuring flags |
| Financial Analysis | `R001–R007` | Growth, profitability, leverage and interest burden |
| Behavioural Analysis | `B001–B004` | Utilization, overdraft duration, payment delays and exposure growth |
| Debt Sustainability | `DS001–DS003` | CFADS, debt service and debt-service buffer |

Financial rule status follows the explicit policy:

| Condition | Status |
|---|---|
| 2+ triggered rules | `CRITICAL` |
| Exactly 1 triggered rule | `ATTENTION` |
| No triggered rules + at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty rule-result set | `NORMAL` |

At case level:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 ATTENTION section        → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward the two-area threshold, while `CRITICAL` can still make the final assessment `CRITICAL`.

`NOT_EVALUABLE` is intentionally different from `NOT_TRIGGERED`: insufficient evidence must not silently become evidence of normal credit quality.

## Rule Catalogue

Rule configuration is split by assessment domain rather than stored in a single legacy registry file:

- [`config/financial_analysis_rules.yaml`](config/financial_analysis_rules.yaml) — `R001–R007`
- [`config/behavioural_analysis_rules.yaml`](config/behavioural_analysis_rules.yaml) — `B001–B004`
- [`config/debt_sustainability_rules.yaml`](config/debt_sustainability_rules.yaml) — `DS001–DS003`
- [`config/customer_profile_rules.yaml`](config/customer_profile_rules.yaml) — `CP001–CP002`
- [`config/final_assessment.yaml`](config/final_assessment.yaml) — final aggregation policy

### Financial rules

| Rule | Indicator |
|---|---|
| `R001` | Revenue growth deterioration |
| `R002` | Negative EBITDA |
| `R003` | EBITDA margin deterioration |
| `R004` | NFP / EBITDA leverage |
| `R005` | Interest expense / EBITDA |
| `R006` | Finished-goods inventory increase / EBITDA |
| `R007` | Interest coverage ratio |

Thresholds, severity and severity direction are configuration-driven. Rule implementations remain responsible for business semantics and calculation logic.

## Streamlit Application

The Results experience follows a progressive analyst-oriented hierarchy:

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

The UI is presentation-only and consumes structured workflow outputs. It does not recalculate thresholds, severity or assessment status.

### Risk Drivers

Risk Drivers surfaces triggered deterministic indicators across macro-areas and orders them by configured severity priority. It is a **descriptive evidence view**, not an additional risk score.

### Rule Engine Evidence

The evidence view exposes rule-outcome and severity distributions, a filterable rule catalogue and individual rule details. Technical detail is progressively disclosed so the executive assessment remains compact.

### Demo scenario

The repository includes a predefined **Complete Credit Assessment** synthetic scenario. It populates all assessment domains so the Results page can demonstrate the full deterministic rule inventory end-to-end.

No production or confidential banking data is required by the demo.

## AI-Assisted Reporting

The reporting layer supports:

| Mode | Behaviour |
|---|---|
| **Deterministic** | Template-based narrative with no external model |
| **Gemini + Fallback** | External LLM narrative with deterministic fallback |
| **Ollama + Fallback** | Local LLM narrative with deterministic fallback |

The LLM receives controlled assessment evidence and is not asked to calculate the credit status. It must preserve material supplied values and findings and must not invent unsupported causes or facts.

When strict indicator grounding is enabled, required deterministic indicator values are checked in the generated narrative. A grounding failure activates the deterministic fallback.

```text
Primary Generator
      ↓
 Success → Report
      │
    Failure / invalid grounding
      ↓
Deterministic Fallback
```

Failure of the optional AI path never changes the deterministic assessment.

## Execution Observability

Successful workflow executions expose immutable execution metadata, including:

- execution identifier;
- UTC timestamp;
- reporting mode;
- generator used;
- fallback state;
- classified error category where applicable;
- phase and total execution timings.

These fields describe workflow provenance and do not participate in credit decisioning.

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── config.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   ├── assessment.py
│   │   ├── assessment_configuration.py
│   │   ├── charts.py
│   │   ├── components.py
│   │   ├── input/
│   │   └── results/
│   │       ├── case_overview.py
│   │       ├── dashboard.py
│   │       ├── decision_bridge.py
│   │       ├── evidence.py
│   │       ├── executive_synthesis.py
│   │       ├── final_assessment.py
│   │       └── risk_drivers.py
│   └── workflow/
│       ├── assessment_workflow_factory.py
│       └── runner.py
├── config/
│   ├── financial_analysis_rules.yaml
│   ├── behavioural_analysis_rules.yaml
│   ├── debt_sustainability_rules.yaml
│   ├── customer_profile_rules.yaml
│   └── final_assessment.yaml
├── src/
│   ├── agents/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   ├── rules/
│   └── services/
├── docs/
├── tests/
├── requirements.txt
└── README.md
```

## Installation

### Requirements

- Python 3.13+
- Git
- Optional: Ollama for local LLM reporting

```bash
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
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

Provide the API key through an environment variable or Streamlit secrets:

```bash
export GEMINI_API_KEY="your-api-key"
```

### Ollama

Configure the local endpoint/model through environment variables when using the Ollama path:

```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen3:0.6b"
```

## Testing and CI

The repository contains unit, integration, workflow, LLM, model, rule, service and UI tests. The test suite protects both functional behaviour and architectural boundaries.

The GitHub Actions workflow runs on Python **3.13 and 3.14** and applies these quality gates:

```text
Ruff
  ↓
Mypy
  ↓
Pytest + coverage
```

The configured coverage gate is **95% for `src`**.

Run locally:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture, deterministic boundaries, case domains and current Results UI.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — accepted architectural decisions and their rationale.
- [`docs/validation.md`](docs/validation.md) — validation strategy, deterministic invariants, grounding, resilience and CI gates.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — input integrity, secrets, data minimization, LLM trust boundaries and production limitations.

## Design Principles

- **Deterministic decision logic** — explicit rules own the credit judgement.
- **Structural input validation** — malformed positions are rejected before assessment.
- **Explicit data availability** — `NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.
- **Explainability by design** — quantitative evidence remains traceable.
- **Domain separation** — customer profile, financial, behavioural and debt-sustainability logic remain explicit.
- **Configuration over hard-coding** — thresholds and aggregation policy are externalized.
- **AI as a bounded reporting layer** — LLMs generate narrative, not decisions.
- **Grounded generation** — material deterministic evidence is protected by explicit contracts.
- **Resilience** — AI reporting can fall back deterministically.
- **Auditability** — execution provenance is separate from decision data.
- **Progressive disclosure** — executive information is visible first; technical evidence is available on demand.

## Roadmap

- [x] Deterministic financial Rule Engine
- [x] Configurable rule thresholds and severity
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` handling
- [x] Customer Profile assessment
- [x] Financial Analysis assessment
- [x] Behavioural Analysis assessment
- [x] Debt Sustainability assessment
- [x] Deterministic final case aggregation
- [x] Explainable rule evidence
- [x] Risk Drivers visualization
- [x] Rule Engine evidence view
- [x] Executive Results hierarchy
- [x] LLM-assisted reporting
- [x] Gemini integration
- [x] Local Ollama integration
- [x] Deterministic LLM fallback
- [x] LLM grounding and indicator validation
- [x] LLM error classification and failure-path testing
- [x] Execution observability and provenance metadata
- [x] Automated CI validation on Python 3.13 and 3.14
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring and evaluation metrics
- [ ] Additional rule families and external data sources

## Current Baseline

The current `main` branch reflects the completed multi-domain case structure, integrated demo data flow, evidence-oriented Results experience and recent simplification of Risk Drivers presentation. The Risk Drivers view no longer exposes the removed threshold-distance metric; ordering is based on deterministic severity priority.

The latest implementation also ensures that the predefined demo scenario supplies its customer-profile, behavioural and debt-sustainability inputs to the assessment workflow, allowing the complete configured rule inventory to be exercised in the application.

The deterministic Rule Engine and case-level aggregation remain the sole source of truth. LLM components remain optional and non-decisional.

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, explainability and applied AI**.
