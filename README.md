# Credit Assessment System

> Deterministic, multi-domain credit-risk assessment with controlled AI-assisted reporting.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** evaluates a synthetic credit position through explicit, configurable rules across four assessment domains and presents the resulting evidence through Streamlit.

> **The deterministic system decides; AI explains.**

Decisioning, analysis, reporting and presentation are separate concerns. Gemini and local Ollama are optional reporting providers and cannot change status, thresholds, severity, findings, limitations or the final decision.

## Assessment Model

The current catalogue contains **18 rules across four domains**:

| Domain | Rule IDs | Count |
|---|---|---:|
| Customer Profile | `CP001–CP004` | 4 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Canonical order: **Customer Profile → Financial Analysis → Behavioural Analysis → Debt Sustainability**.

For rule-based sections:

| Condition | Status |
|---|---|
| 2+ triggered rules | `CRITICAL` |
| Exactly 1 triggered rule | `ATTENTION` |
| No triggered rules + evaluable evidence | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

At case level, `CRITICAL` propagates directly; two or more core `ATTENTION` sections escalate to `CRITICAL`; one core `ATTENTION` produces `ATTENTION`; otherwise the case is `NORMAL`. If no section is evaluable, the case is `ATTENTION`.

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward that threshold, while `CRITICAL` can still produce a `CRITICAL` case.

`NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.

## Architecture

```text
CreditPosition
     ↓
Input Validation
     ↓
Four Domain Assessments
     ↓
CreditAssessmentCase
     ↓
Final Assessment
     ↓
Deterministic Analysis
     ↓
Reporting Agent
   ↙       ↘
Deterministic  Optional LLM
 Generator     Gemini / Ollama
      ↘       ↙
        Report
```

The core implementation is under `src/`; Streamlit presentation and application orchestration are under `app/`.

## Configuration

Rules are configured by domain under `config/`:

```text
config/
├── customer_profile_rules.yaml
├── financial_analysis_rules.yaml
├── behavioural_analysis_rules.yaml
├── debt_sustainability_rules.yaml
└── final_assessment.yaml
```

Thresholds, severity and severity direction are configuration-driven. Rule and domain implementations contain the corresponding business semantics.

## Results UI

The Results page follows a compact hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

The macro-area dashboard is the authoritative deterministic evidence surface. Technical inspection is progressively disclosed through **Rule Catalogue & Filters** and **Individual Rule Detail**.

Separate bottom-of-page Risk Drivers and Detailed Assessment sections are not rendered. The UI does not recalculate rules or decisions.

## AI-Assisted Reporting

| Mode | Behaviour |
|---|---|
| **Deterministic** | Model-independent deterministic narrative |
| **Gemini + Fallback** | Gemini narrative with deterministic fallback |
| **Ollama + Fallback** | Local Ollama narrative with deterministic fallback |

The LLM receives deterministic evidence and generates prose only. Grounding validation can reject an invalid narrative and activate deterministic fallback.

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

The Executive Narrative always follows the application-controlled order of the four domains.

## Execution Metadata

Workflow execution metadata records provenance such as execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and timings. It is observational and does not participate in decisioning.

## Demo Data

Demonstration data is synthetic/anonymized and covers the configured assessment domains and rule inventory, including the Customer Profile forborne exposure indicator. Production or confidential banking data must not be committed to the repository.

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   ├── input/
│   │   └── results/
│   └── workflow/
├── config/
├── src/
│   ├── agents/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   ├── rules/
│   │   ├── base/
│   │   ├── customer_profile/
│   │   ├── financial_analysis/
│   │   ├── behavioural/
│   │   └── sustainability/
│   └── services/
├── docs/
├── tests/
├── requirements.txt
└── README.md
```

Legacy rule trees and compatibility UI/test paths are not part of the current architecture.

## Installation

### Requirements

- Python **3.14**
- Git
- Optional: Ollama for local reporting

```bash
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
cd credit-assessment-system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app/streamlit_app.py
```

Configure `GEMINI_API_KEY` through an environment variable or Streamlit secrets when Gemini reporting is enabled. Configure Ollama according to the local installation when local reporting is enabled.

## Testing and CI

The test suite mirrors the source architecture and covers rules, models, services, agents, workflow, reporting, application UI and integration boundaries.

GitHub Actions targets **Python 3.14** and runs:

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

- [`docs/README.md`](docs/README.md) — documentation map and maintenance rules.
- [`docs/architecture.md`](docs/architecture.md) — current architecture, domains, workflow, configuration and UI.
- [`docs/reporting.md`](docs/reporting.md) — deterministic evidence flow and bounded reporting.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — architectural decisions and rationale.
- [`docs/adr-016-complete-rule-evidence-reporting.md`](docs/adr-016-complete-rule-evidence-reporting.md) — complete rule-evidence propagation into reporting.
- [`docs/validation.md`](docs/validation.md) — validation strategy, testing and CI.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — security and data-handling principles.

## Design Principles

- **Deterministic decision logic** — rules own the credit judgement.
- **Domain separation** — four assessment domains remain explicit.
- **Configuration over hard-coding** — policy parameters are externalized.
- **Explicit data availability** — `NOT_EVALUABLE` is not normal evidence.
- **Explainability** — rule evidence remains traceable.
- **AI as bounded reporting** — LLMs generate narrative, not decisions.
- **Grounded generation** — narrative is constrained by deterministic evidence.
- **Resilience** — reporting can fall back deterministically.
- **Thin presentation** — Streamlit consumes assessment results rather than implementing credit logic.

## Roadmap

- [x] Deterministic multi-domain assessment
- [x] 18 configured rules across four domains
- [x] Configurable thresholds and severity
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` handling
- [x] Deterministic final aggregation
- [x] Explainable rule evidence
- [x] Compact macro-area Results dashboard
- [x] Application-controlled Executive Narrative
- [x] Gemini integration
- [x] Local Ollama integration
- [x] Deterministic LLM fallback
- [x] LLM grounding validation
- [x] Execution observability
- [x] CI on Python 3.14
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring/evaluation metrics
- [ ] Additional rule families and external data sources

## Current Baseline

The `main` branch is the current thesis-ready baseline: four deterministic assessment domains, 18 configured rules, deterministic case aggregation, synthetic demonstration data, a compact evidence-oriented Results experience and bounded optional LLM reporting.

The architecture keeps assessment independent from Streamlit and from every LLM provider. The application decides first; reporting explains the resulting evidence afterward.

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI
