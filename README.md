# Credit Assessment System

> Production-oriented credit-risk assessment prototype combining deterministic rule-based decisioning, multi-domain assessment, explainable evidence and bounded LLM-assisted reporting.

[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** evaluates a synthetic credit position through deterministic, configurable rules and presents the evidence through an analyst-oriented Streamlit application.

The central architectural principle is:

> **The system decides; AI explains.**

The deterministic assessment is the sole source of truth. Gemini and local Ollama are optional reporting providers and cannot modify status, severity, thresholds, findings, limitations or final decisions.

## Architecture at a Glance

```text
Credit Position + Case Inputs
          ↓
Structural Validation
          ↓
Deterministic Domain Assessment
   ┌──────┼──────────┬──────────────┐
   ↓      ↓          ↓              ↓
Customer Financial Behavioural  Debt Sustainability
Profile  Analysis  Analysis      Analysis
CP001-3  R001-7    B001-4        DS001-3
   └──────┼──────────┴──────────────┘
          ↓
CreditAssessmentCase
          ↓
FinalAssessmentService
          ↓
Deterministic Analysis
          ↓
Reporting / optional LLM
          ↓
Report + Execution Metadata
```

The application deliberately separates **decisioning**, **analysis**, **reporting** and **presentation**.

## Assessment Model

The current configured inventory contains **17 rules across four domains**:

| Domain | Rules | Count |
|---|---|---:|
| Customer Profile | `CP001–CP003` | 3 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Canonical order:

**Customer Profile → Financial Analysis → Behavioural Analysis → Debt Sustainability**

For rule-based sections:

| Condition | Status |
|---|---|
| 2+ triggered rules | `CRITICAL` |
| Exactly 1 triggered rule | `ATTENTION` |
| No triggered rules + evaluable evidence | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

At case level, any `CRITICAL` section produces `CRITICAL`; two or more core `ATTENTION` sections escalate to `CRITICAL`; one `ATTENTION` produces `ATTENTION`; otherwise the case is `NORMAL`, unless no section is evaluable, in which case it is `ATTENTION`.

Customer Profile is contextual for the two-core-area escalation: its `ATTENTION` status does not count toward the two-area threshold, while `CRITICAL` can still produce a `CRITICAL` case.

`NOT_EVALUABLE` is explicitly distinct from `NOT_TRIGGERED`.

## Rule Catalogue

Configuration is separated by domain:

- [`config/customer_profile_rules.yaml`](config/customer_profile_rules.yaml) — `CP001–CP003`
- [`config/financial_analysis_rules.yaml`](config/financial_analysis_rules.yaml) — `R001–R007`
- [`config/behavioural_analysis_rules.yaml`](config/behavioural_analysis_rules.yaml) — `B001–B004`
- [`config/debt_sustainability_rules.yaml`](config/debt_sustainability_rules.yaml) — `DS001–DS003`
- [`config/final_assessment.yaml`](config/final_assessment.yaml) — final aggregation policy

Thresholds, severity and severity direction are configuration-driven; business semantics remain in the rule/domain implementations.

## Streamlit Results Experience

The current Results page is intentionally compact and non-redundant:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

### Executive Credit Assessment

The page opens with the deterministic final status and three KPIs:

- rules evaluated;
- triggered rules;
- not-evaluable rules.

Reporting provenance is shown only as lightweight metadata.

### Assessment by Macro-Area

The dashboard displays the four authoritative `AssessmentSection` outcomes once, with compact evidence counts and the most relevant indicators.

Technical inspection is progressively disclosed inside the evidence dashboard through:

- **Rule Catalogue & Filters**;
- **Individual Rule Detail**.

Redundant aggregate charts and separate bottom-of-page Risk Drivers / Detailed Assessment sections are no longer part of the Results flow.

### Executive Narrative

The narrative follows the deterministic macro-area order. **Python controls titles and structure; the LLM supplies prose only.** The visible section title is simply **Executive Narrative**.

The UI is presentation-only and never recalculates thresholds, severity or assessment status.

## AI-Assisted Reporting

Supported modes:

| Mode | Behaviour |
|---|---|
| **Deterministic** | Template-based narrative |
| **Gemini + Fallback** | Gemini narrative with deterministic fallback |
| **Ollama + Fallback** | Local Ollama narrative with deterministic fallback |

Current conservative generation settings:

- Gemini temperature: `0.1`;
- Gemini thinking: `MINIMAL`;
- Gemini `max_output_tokens`: `8192`;
- Ollama temperature: `0.2`;
- Ollama thinking: disabled.

The LLM is not part of the decision path. Grounding validation can reject an invalid narrative and activate deterministic fallback.

```text
Deterministic Evidence
        ↓
Primary Generator
        ↓
Grounding Validation
    ↙           ↘
 valid        invalid/failure
   ↓               ↓
 Report      Deterministic Fallback
```

## Execution Observability

Workflow executions expose immutable provenance metadata such as execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and phase/total timings. Observability does not participate in credit decisioning.

## Demo Data

The repository contains a synthetic **Complete Credit Assessment** scenario covering all four domains and the configured rule inventory end-to-end.

No production or confidential banking data is required or embedded in the project.

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   └── results/
│   │       ├── dashboard.py
│   │       ├── executive_synthesis.py
│   │       ├── case_overview.py
│   │       └── final_assessment.py
│   └── workflow/
├── config/
│   ├── customer_profile_rules.yaml
│   ├── financial_analysis_rules.yaml
│   ├── behavioural_analysis_rules.yaml
│   ├── debt_sustainability_rules.yaml
│   └── final_assessment.yaml
├── src/
│   ├── agents/
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

Run Streamlit:

```bash
streamlit run app/streamlit_app.py
```

For Gemini:

```bash
export GEMINI_API_KEY="your-api-key"
```

For Ollama:

```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen3:0.6b"
```

## Testing and CI

The project uses unit, integration, workflow, rule, service, model, LLM and UI tests.

GitHub Actions validates Python **3.13 and 3.14** with:

```text
Ruff → Mypy → Pytest + coverage
```

The coverage gate is **95% for `src`**.

Local checks:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture, domain boundaries, decision/reporting separation and current Results UI.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — accepted architectural decisions and rationale.
- [`docs/validation.md`](docs/validation.md) — deterministic invariants, rule/scenario coverage, LLM grounding, resilience and CI gates.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — input integrity, secrets, data minimization and LLM trust boundaries.

## Design Principles

- **Deterministic decision logic** — explicit rules own the credit judgement.
- **Structural validation** — malformed input is rejected before assessment.
- **Explicit data availability** — `NOT_EVALUABLE` is not treated as normal evidence.
- **Explainability** — structured evidence remains traceable.
- **Domain separation** — four assessment domains remain explicit.
- **Configuration over hard-coding** — thresholds and aggregation policy are externalized.
- **AI as bounded reporting** — LLMs generate narrative, not decisions.
- **Grounded generation** — material deterministic evidence is protected.
- **Resilience** — AI reporting can fall back deterministically.
- **Progressive disclosure** — executive information is visible first; technical evidence is available on demand.

## Roadmap

- [x] Deterministic multi-domain assessment
- [x] 17 configured rules across four domains
- [x] Configurable thresholds and severity
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` handling
- [x] Deterministic final aggregation
- [x] Explainable rule evidence
- [x] Compact macro-area Results dashboard
- [x] Executive Narrative with deterministic macro-area order
- [x] Gemini integration
- [x] Local Ollama integration
- [x] Deterministic LLM fallback
- [x] LLM grounding and indicator validation
- [x] Execution observability
- [x] Automated CI on Python 3.13 and 3.14
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring/evaluation metrics
- [ ] Additional rule families and external data sources

## Current Baseline

The current `main` branch is the **thesis-ready multi-domain baseline**: four deterministic assessment domains, 17 configured rules, deterministic case aggregation, synthetic demo data, a compact evidence-oriented Results experience and bounded optional LLM reporting.

The Results UI now shows the deterministic macro-area outcomes once, followed by the Executive Narrative. Technical rule inspection remains available inside the evidence dashboard; separate bottom-of-page Risk Drivers and Detailed Assessment sections have been removed to keep the analyst workflow focused.

The Executive Narrative uses the fixed order **Customer Profile → Financial Analysis → Behavioural Analysis → Debt Sustainability**. Titles are application-controlled and provider-independent.

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI

This project explores the intersection of **credit risk assessment, data-driven decision systems, explainability and applied AI**.
