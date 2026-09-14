# Credit Assessment System

> Deterministic, multi-domain credit-risk assessment with controlled AI-assisted reporting.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** evaluates a credit position through explicit, configurable deterministic rules organised by assessment domain and presents the resulting evidence through Streamlit.

> **The deterministic system decides; AI explains.**

Decisioning, analysis, reporting and presentation are separate concerns. Optional LLM providers can generate narrative, but cannot change the structured assessment.

The repository is designed so that the rule catalogue can evolve without requiring rule-specific changes in central services, reporting or presentation code.

## Architecture

```text
CreditPosition
     ↓
Structural Validation
     ↓
Domain Assessments
     ↓
CreditAssessmentCase
     ↓
FinalAssessmentService
     ↓
Deterministic Analysis
     ↓
Reporting Agent
   ↙          ↘
Deterministic  Optional LLM
 Generator       Provider
      ↘          ↙
        Report
```

The core implementation is under `src/`. Streamlit presentation and application orchestration are under `app/`.

### Deterministic boundary

```text
Rule configuration
       ↓
Rule implementation
       ↓
Automatic discovery / registry
       ↓
RuleResult
       ↓
Domain assessment
       ↓
Final assessment
```

The deterministic path is the source of truth for credit evidence and status.

### Reporting boundary

```text
Deterministic Evidence
        ↓
Primary Reporting Generator
        ↓
Grounding Validation
    ↙           ↘
 valid        invalid/failure
   ↓               ↓
 Report      Deterministic Fallback
```

An LLM or grounding failure affects only the reporting path. It cannot invalidate or replace the deterministic assessment.

## Rule catalogue

Rules are organised by assessment domain. The active inventory is defined by the YAML catalogues under `config/` and the registered implementations discovered under `src/rules/`.

The README deliberately does **not** maintain a duplicated list of rule IDs, rule counts or thresholds. Those values are catalogue data and can change independently of the architecture.

The rule contract is:

```text
Configured rule identifier
            ↓
Registered deterministic implementation
            ↓
RuleResult
```

Every configured identifier must resolve to one concrete implementation. Missing or duplicate registrations should fail validation rather than silently dropping a rule.

See **[`docs/rules.md`](docs/rules.md)** for the complete procedure for designing and adding a rule.

## Configuration

```text
config/
├── <domain>_rules.yaml
└── final_assessment.yaml
```

Rule configuration contains declarative parameters such as input fields, calculation type, trigger operator, threshold, severity, severity direction, severity bands and comment templates.

The final-assessment configuration contains aggregation policy. Keeping policy outside the presentation layer makes changes reviewable and prevents thresholds from being duplicated across the application.

## Adding a New Rule

Adding a rule is an **end-to-end change**, not a YAML-only change:

```text
Business requirement
        ↓
Input contract
        ↓
Domain configuration
        ↓
Concrete Rule implementation
        ↓
Automatic discovery + registry
        ↓
RuleEngine / domain service
        ↓
RuleResult
        ↓
Section / case aggregation
        ↓
Analysis evidence
        ↓
Reporting / grounding
        ↓
Demo / UI
        ↓
Tests
```

The complete checklist is maintained in [`docs/rules.md`](docs/rules.md). It covers business semantics, input modelling, configuration, implementation, discovery, `NOT_EVALUABLE`, severity, aggregation, reporting, grounding, demo data, UI, tests and documentation.

## Rule design principles

- **Deterministic:** a rule produces the same result for the same input and configuration.
- **Explicit:** `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` remain distinct.
- **Configurable:** thresholds and other policy parameters are externalised when generic configuration is sufficient.
- **Extensible:** new rules use the registry/discovery mechanism instead of central branching.
- **Traceable:** rule evidence remains available to downstream analysis and reporting.
- **Isolated:** individual rules do not own section or case aggregation.
- **AI-independent:** no LLM participates in deterministic rule evaluation.

## Results UI

The Results experience presents workflow output through a compact hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

The macro-area evidence surface is authoritative for presentation. Technical rule inspection uses the same structured results.

The UI does not recalculate rule thresholds, severity or assessment status.

## AI-assisted reporting

The application supports a deterministic reporting path and can expose configured external or local LLM providers depending on the execution environment.

The reporting layer:

- consumes deterministic evidence;
- generates narrative only;
- preserves material findings and indicators;
- applies grounding validation where required;
- falls back deterministically when the primary reporting path fails.

The reporting layer must never become a second decision engine.

## Data and security

Demonstration data is synthetic/anonymized. Production or confidential banking data must not be committed to the repository.

Credentials must be supplied through environment/secret configuration rather than source code. External LLM use must comply with the applicable data-classification and governance requirements.

See [`docs/security-data-handling.md`](docs/security-data-handling.md).

## Project structure

```text
credit-assessment-system/
├── app/                 # UI and application orchestration
├── config/              # Declarative assessment configuration
├── src/
│   ├── agents/          # Analysis and reporting orchestration
│   ├── comments/        # Deterministic comments/evidence support
│   ├── config/          # Configuration and policy models/loaders
│   ├── engine/          # Rule execution
│   ├── llm/             # LLM abstraction and providers
│   ├── models/          # Domain/workflow models
│   ├── rules/           # Rule base, discovery, registry and implementations
│   └── services/        # Assessment and workflow services
├── docs/                # Architecture, rules, validation, security and ADRs
├── tests/               # Unit/integration/workflow/reporting/UI tests
├── pyproject.toml
├── requirements.txt
└── README.md
```

The repository tree is authoritative. Documentation avoids enumerating individual source files that are expected to evolve.

## Installation

### Requirements

- Python version supported by the repository CI (currently Python 3.14)
- Git
- Optional local LLM runtime when using local reporting

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

LLM credentials and provider settings are environment/deployment configuration. Do not commit secrets.

## Testing and CI

Run the repository quality checks locally:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

The CI workflow is the authoritative definition of supported Python versions, commands and coverage requirements. If those settings change, update this section accordingly rather than treating README values as policy.

## Documentation

- [`docs/README.md`](docs/README.md) — documentation map and maintenance principles.
- [`docs/architecture.md`](docs/architecture.md) — system architecture and boundaries.
- [`docs/rules.md`](docs/rules.md) — complete rule-development lifecycle.
- [`docs/reporting.md`](docs/reporting.md) — reporting and evidence contract.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — architectural decision index and rationale.
- [`docs/adr-016-complete-rule-evidence-reporting.md`](docs/adr-016-complete-rule-evidence-reporting.md) — complete rule-evidence reporting decision.
- [`docs/adr-017-rule-implementation-configuration-separation.md`](docs/adr-017-rule-implementation-configuration-separation.md) — rule configuration/implementation separation.
- [`docs/validation.md`](docs/validation.md) — validation strategy and quality gates.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — security and data-handling principles.

## Design principles

1. Deterministic decision logic owns credit assessment.
2. Rule policy is externalised where it can be expressed declaratively.
3. Individual rules do not implement final case aggregation.
4. Missing evidence is explicit and never silently treated as normal evidence.
5. Structured evidence is preserved across workflow boundaries.
6. LLMs are bounded reporting components, not decision engines.
7. Generated narrative is grounded and treated as untrusted output.
8. Deterministic fallback preserves reporting resilience.
9. Streamlit remains a presentation/application layer.
10. Documentation describes stable contracts rather than duplicating volatile catalogue data.

## Roadmap

- [x] Deterministic multi-domain assessment
- [x] Externalised rule configuration
- [x] Automatic rule discovery and registry
- [x] Structural input validation
- [x] Explicit non-evaluable handling
- [x] Deterministic final assessment policy
- [x] Complete rule evidence for reporting
- [x] Grounded optional LLM reporting
- [x] Deterministic reporting fallback
- [x] Execution provenance
- [x] Automated quality checks
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring/evaluation metrics
- [ ] Additional rule families and external data sources

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI
