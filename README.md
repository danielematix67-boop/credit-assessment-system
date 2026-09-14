# Credit Assessment System

> A production-oriented credit-risk assessment prototype combining deterministic rule-based decisioning, multi-domain case assessment, explainable evidence, resilient LLM-assisted reporting and execution observability.

[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** evaluates a synthetic credit position through deterministic, configurable rules and presents the resulting evidence through an analyst-oriented Streamlit interface.

The architecture deliberately separates **credit decision-making from AI-generated communication**:

- `CreditPositionValidator` validates structural input before assessment;
- deterministic domain services evaluate the configured indicators;
- the four assessment domains are consolidated into a deterministic `CreditAssessmentCase`;
- `FinalAssessmentService` performs deterministic cross-domain aggregation;
- analysis components organize deterministic findings and limitations;
- reporting supports deterministic, Gemini and local Ollama narratives;
- LLM output is bounded by an explicit grounding contract and deterministic fallback;
- immutable execution metadata records reporting provenance and timings.

> **Core principle: the system decides; AI explains. The LLM has no authority over the credit judgement.**

## Architecture at a Glance

```text
Credit Position + Case Inputs
          ↓
Structural Validation
          ↓
Deterministic Case Assessment
          ├── Customer Profile → CP001–CP003
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

The application evaluates four explicit deterministic domains and **17 configured rules**:

| Domain | Rule family | Rules | Purpose |
|---|---|---:|---|
| Customer Profile | `CP001–CP003` | 3 | EWS, restructuring history and business history |
| Financial Analysis | `R001–R007` | 7 | Growth, profitability, leverage and interest burden |
| Behavioural Analysis | `B001–B004` | 4 | Utilization, overdraft duration, payment delays and exposure growth |
| Debt Sustainability | `DS001–DS003` | 3 | CFADS, debt service and debt-service buffer |

The canonical presentation order is **Customer Profile → Financial Analysis → Behavioural Analysis → Debt Sustainability**.

### Deterministic status policy

For a rule-based section:

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

Rule configuration is split by assessment domain:

- [`config/customer_profile_rules.yaml`](config/customer_profile_rules.yaml) — `CP001–CP003`
- [`config/financial_analysis_rules.yaml`](config/financial_analysis_rules.yaml) — `R001–R007`
- [`config/behavioural_analysis_rules.yaml`](config/behavioural_analysis_rules.yaml) — `B001–B004`
- [`config/debt_sustainability_rules.yaml`](config/debt_sustainability_rules.yaml) — `DS001–DS003`
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

The Results experience follows a progressive, non-redundant analyst hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
          ↓
Risk Drivers (collapsed)
          ↓
Detailed Assessment (collapsed)
          ↓
Rule Catalogue & Filters (collapsed)
          ↓
Individual Rule Detail (collapsed)
```

The four macro-areas are displayed once as the authoritative deterministic overview. The UI is presentation-only and does not recalculate thresholds, severity or assessment status.

### Assessment by Macro-Area

The dashboard presents the deterministic outcome for Customer Profile, Financial Analysis, Behavioural Analysis and Debt Sustainability, including compact rule/evidence counts and the most relevant indicators.

### Risk Drivers

Risk Drivers surfaces triggered deterministic indicators across macro-areas and orders them by configured severity priority. It is a **descriptive evidence view**, not an additional risk score.

### Executive Narrative

The Executive Narrative is generated from deterministic evidence. Python controls the macro-area titles and their canonical order; Gemini/Ollama provide narrative synthesis only.

### Detailed Assessment

The detailed view is an analyst/audit surface for customer context, domain-specific evidence, findings, limitations and data-quality information. It does not repeat the executive status or recreate the macro-area decision logic.

### Rule Engine Evidence

Technical rule inspection is progressively disclosed through a filterable catalogue and individual rule details. The evidence view is intentionally lean and does not duplicate the macro-area dashboard with additional aggregate charts.

## Demo Scenario

The repository includes a predefined synthetic **Complete Credit Assessment** scenario. It supplies inputs for all four assessment domains so the application can exercise the complete configured rule inventory end-to-end.

The demo uses no production or confidential banking data.

## AI-Assisted Reporting

The reporting layer supports:

| Mode | Behaviour |
|---|---|
| **Deterministic** | Template-based narrative with no external model |
| **Gemini + Fallback** | External LLM narrative with deterministic fallback |
| **Ollama + Fallback** | Local LLM narrative with deterministic fallback |

The LLM receives controlled assessment evidence and is never asked to calculate the credit status. It must preserve material supplied values and findings and must not invent unsupported causes or facts.

The current default generation configuration is deliberately conservative:

- Gemini temperature: `0.1`;
- Gemini thinking level: `MINIMAL`, without exposed thoughts;
- Gemini maximum output tokens: `8192`;
- Ollama temperature: `0.2`;
- Ollama thinking: disabled.

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
│   ├── customer_profile_rules.yaml
│   ├── financial_analysis_rules.yaml
│   ├── behavioural_analysis_rules.yaml
│   ├── debt_sustainability_rules.yaml
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

GitHub Actions validates Python **3.13 and 3.14** through:

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

- [`docs/architecture.md`](docs/architecture.md) — system architecture, deterministic boundaries, four assessment domains and current Results UI.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — accepted architectural decisions and their rationale.
- [`docs/validation.md`](docs/validation.md) — validation strategy, deterministic invariants, grounding, resilience, scenario coverage and CI gates.
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

- [x] Deterministic multi-domain Rule Engine / assessment services
- [x] Configurable rule thresholds and severity
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` handling
- [x] Customer Profile assessment
- [x] Financial Analysis assessment
- [x] Behavioural Analysis assessment
- [x] Debt Sustainability assessment
- [x] Deterministic final case aggregation
- [x] Explainable rule evidence
- [x] Severity-based Risk Drivers visualization
- [x] Progressive-disclosure Results experience
- [x] Executive Narrative with deterministic macro-area order
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

The current `main` branch represents the **thesis-ready multi-domain baseline**: four deterministic assessment domains, 17 configured rules, deterministic case aggregation, integrated synthetic demo data, an evidence-oriented Results experience and bounded optional LLM reporting.

The Results UI has been simplified so that macro-area outcomes are shown once, Risk Drivers remain a secondary evidence view, Detailed Assessment is an analyst/audit drill-down, and technical rule inspection is progressively disclosed.

The Executive Narrative uses the fixed order **Customer Profile → Financial Analysis → Behavioural Analysis → Debt Sustainability**. Titles are application-controlled; the LLM supplies narrative only.

The deterministic Rule Engine/domain services and `FinalAssessmentService` remain the sole source of truth. AI components are optional, replaceable and non-decisional.

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, explainability and applied AI**.
