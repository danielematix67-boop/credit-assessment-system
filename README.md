# Credit Assessment System

> **A deterministic credit-risk assessment engine with controlled AI-assisted reporting.**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

**Credit Risk · Python · Rule Engine · YAML Configuration · Data Analytics · AI-assisted Reporting**

> **The deterministic system decides; AI explains.**

[**▶ Open the Streamlit demo**](https://credit-assessment-system.streamlit.app/)

---

## 🎯 What is this project?

Credit Assessment System is a prototype credit-risk platform designed to evaluate a credit position through **explicit, configurable and testable deterministic rules** and then turn the resulting structured evidence into controlled, grounded reporting.

The project combines four perspectives:

- **Credit Risk:** financial, behavioural, customer and debt-sustainability evidence.
- **Data Analytics:** indicators, thresholds, severity and structured evidence.
- **Software Engineering:** configuration-driven rules, automatic discovery, validation and testing.
- **AI:** optional narrative generation that remains strictly downstream of the deterministic assessment.

The important architectural principle is simple:

> **AI can explain the assessment, but it cannot make or modify the assessment.**

---

## 👀 Understand it in 30 seconds

```text
                         CREDIT POSITION
                                │
                                ▼
                     Structural Validation
                                │
                                ▼
                     Deterministic Rule Engine
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
              Rule Results          Domain Statuses
                     │                     │
                     └──────────┬──────────┘
                                ▼
                      Final Assessment Policy
                                │
                                ▼
                     Deterministic Evidence
                                │
                                ▼
                       Reporting Agent
                         ↙           ↘
                  LLM generator    Fallback
                         ↘           ↙
                            Report
```

The deterministic path is the **source of truth**. The reporting path consumes its structured evidence and produces narrative only.

---

## 🧭 Project at a glance

| Area | Role |
|---|---|
| **Business domain** | Credit Risk / Credit Assessment |
| **Core engine** | Deterministic Rule Engine |
| **Configuration** | YAML-driven rule and assessment policy |
| **Backend** | Python |
| **Application** | Streamlit |
| **Testing** | pytest |
| **Quality** | Ruff + mypy + coverage gate |
| **AI** | Optional reporting layer |
| **Data** | Synthetic demonstration data |
| **Deployment** | Streamlit-compatible |

---

## 🏦 Business problem

Credit assessment requires combining heterogeneous evidence while keeping the final judgement **traceable, reproducible and explainable**.

A useful system therefore needs to answer questions such as:

1. Which indicators were evaluated?
2. Which rules were triggered?
3. Which evidence could not be evaluated?
4. How did domain-level results contribute to the overall assessment?
5. Can the result be reproduced from the same inputs and configuration?
6. Can an executive report be generated without allowing a language model to alter the underlying decision?

This project addresses those requirements through a deterministic assessment layer followed by a bounded reporting layer.

---

## 🧠 Why this architecture?

### 1. Deterministic first

Credit assessment is performed by explicit, testable business rules. The same input and configuration produce the same deterministic result.

### 2. AI second

AI is useful for interpretation and communication, but it is not authoritative for the credit decision. A reporting failure must not change the assessment.

### 3. Configuration-driven

Rule parameters and assessment policy are externalised where they can be expressed declaratively. This allows the catalogue to evolve without duplicating thresholds throughout the application.

### 4. Evidence-preserving

Structured rule results remain available throughout the workflow so that the final report can be traced back to deterministic evidence.

---

## 🔄 Assessment workflow

```text
Input
  ↓
CreditPosition
  ↓
Structural validation
  ↓
Configured rules
  ↓
RuleResult
  ↓
Domain assessment
  ↓
Final assessment
  ↓
Deterministic analysis
  ↓
Reporting
  ↓
Executive output
```

Rules explicitly distinguish:

- `TRIGGERED`
- `NOT_TRIGGERED`
- `NOT_EVALUABLE`

Missing evidence is therefore not silently interpreted as a normal result.

---

## 📥 Input sources

The Streamlit application uses **Excel Upload as its sole input source**. Upload a workbook containing one or more scenarios; the application validates the workbook, lets the user select a `scenario_id`, previews the mapped inputs and executes the selected scenario.

The loader recognises these assessment-domain sheets:

| Sheet | Requirement | Cardinality |
|---|---|---|
| `Financial Analysis` | Required | One row per scenario |
| `Customer Profile` | Optional | One row per scenario |
| `Behavioural Analysis` | Optional | One row per scenario |
| `Debt Sustainability` | Optional | One row per scenario |

It also supports three optional detail sheets: `Shareholders`, `Relevant Events` and `Credit Facilities`. These can contain multiple rows per scenario and enrich the Customer Profile context. Every input sheet must include `scenario_id`; identifiers in detail sheets must match a scenario in `Financial Analysis`. The loader rejects malformed workbooks, missing required columns, duplicate scenario identifiers and references to unknown scenarios.

If an optional assessment-domain sheet is absent, its domain input is unavailable; it is not silently treated as normal evidence. A workbook may include a documentation-only `README` sheet, which is ignored by the domain loader.

The accepted field names follow the domain models and loader contract. Rule inventories and thresholds remain defined in configuration and source code rather than duplicated here.

See [`docs/excel-scenario-input.md`](docs/excel-scenario-input.md) for the workbook schema and validation behaviour.

---

## 🤖 Deterministic assessment vs AI reporting

This separation is the central design decision of the project.

| Responsibility | Deterministic layer | AI/reporting layer |
|---|:---:|:---:|
| Evaluate indicators | ✅ | ❌ |
| Apply thresholds | ✅ | ❌ |
| Determine rule severity | ✅ | ❌ |
| Determine assessment status | ✅ | ❌ |
| Preserve limitations | ✅ | ✅ |
| Explain findings | — | ✅ |
| Generate narrative | — | ✅ |
| Change the decision | ❌ | ❌ |

The reporting component is therefore a **consumer of assessment evidence**, not a second assessment engine.

---

## 👤 Customer Profile

Customer Profile combines deterministic rule evidence with descriptive counterparty context. The structured profile is organised into General Information, Risk Profile & Predictiveness, Relationship & Counterparty Context, and Relevant Events.

The Executive Narrative always starts its Customer Profile section with a **fixed, deterministic context block**, independent of reporting mode. Triggered Customer Profile rule findings follow that block. In Deterministic mode, rule findings retain their configured deterministic comments; in Gemini/Ollama modes, the LLM may rewrite the rule findings but cannot rewrite the fixed context or change any assessment result.

The fixed narrative context includes available company information, rating/PD, banking relationship, shareholders and credit facilities. Risk-group interdependence/independence descriptions are excluded. This keeps contextual description distinct from deterministic rule evidence and avoids duplicating profile facts in the narrative.

See [`docs/customer-profile.md`](docs/customer-profile.md) and [`docs/reporting.md`](docs/reporting.md) for the detailed contracts.

---

## 📊 What the application presents

The Streamlit application exposes the workflow through a compact hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

The UI presents structured results but does not recalculate thresholds, severity or assessment status.

For technical inspection, the same underlying rule results remain available to the workflow and reporting layers.

---

## 🖥️ Try the application

**Live demo:** [credit-assessment-system.streamlit.app](https://credit-assessment-system.streamlit.app/)

The demonstration environment uses synthetic data. It is intended to show the assessment workflow and reporting architecture, not to process confidential banking information.

---

## ➕ Adding a new rule

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

The application uses automatic discovery and a registry, so new rules should not require central branching in the Rule Engine, Reporting Agent or Streamlit presentation.

See [`docs/rules.md`](docs/rules.md) for the complete development checklist, including configuration, implementation, `NOT_EVALUABLE`, severity, aggregation, reporting, grounding, demo data and tests.

---

## 🧩 Rule catalogue

The active rule inventory is defined by the valid YAML catalogues under `config/` together with registered implementations discovered under `src/rules/`.

The documentation deliberately does **not** maintain a duplicated list of rule IDs, rule counts, domain-by-domain inventories or thresholds. Those are catalogue data and can evolve independently of the architecture.

The rule contract is:

```text
Configured rule identifier
            ↓
Registered deterministic implementation
            ↓
RuleResult
```

Every configured identifier must resolve to one concrete implementation. Missing or duplicate registrations should fail validation rather than silently dropping a rule.

---

## 🗂️ Project structure

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
├── examples/            # Synthetic demonstration inputs, including Excel
├── docs/                # Architecture, rules, validation, security and ADRs
├── tests/               # Unit/integration/workflow/reporting/UI tests
├── pyproject.toml
├── requirements.txt
└── README.md
```

The repository tree is authoritative. Documentation intentionally avoids enumerating individual source files that are expected to evolve.

The application layer is deliberately separated into interface and workflow concerns. `app/ui/` holds Streamlit views, forms and result renderers, while `app/workflow/` and related orchestration manage execution flow, state and assessment sequencing. Deterministic rule explanations are generated by `src/comments/comment_engine.py`; these are evidence-bearing comments derived from structured rule results, not a second AI decision layer.

---

## 🚀 Quick start

### Requirements

- Python version supported by the repository CI
- Git
- Optional local LLM runtime when using local reporting

### Linux / macOS

```bash
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
cd credit-assessment-system
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

### Windows PowerShell

```powershell
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
cd credit-assessment-system
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

For a more detailed setup and first-run walkthrough, see [`docs/getting-started.md`](docs/getting-started.md).

LLM credentials and provider settings are environment/deployment configuration. Never commit secrets.

---

## 🧪 Testing and quality

Run the repository quality checks locally:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

The CI workflow is the authoritative definition of supported Python versions, commands and quality requirements. README values should be updated if the workflow changes.

---

## 🔐 Data and security

Demonstration data is synthetic. Production or confidential banking data must not be committed to the repository.

Credentials must be supplied through environment or secret configuration rather than source code. External LLM use must comply with applicable data-classification and governance requirements.

See [`docs/security-data-handling.md`](docs/security-data-handling.md).

---

## 📚 Documentation

| Document | Purpose |
|---|---|
| [`docs/getting-started.md`](docs/getting-started.md) | First-run guide for new contributors/readers |
| [`docs/architecture.md`](docs/architecture.md) | System architecture and boundaries |
| [`docs/rules.md`](docs/rules.md) | Complete rule-development lifecycle |
| [`docs/reporting.md`](docs/reporting.md) | Reporting and evidence contract |
| [`docs/customer-profile.md`](docs/customer-profile.md) | Customer Profile fields and materiality policy |
| [`docs/excel-scenario-input.md`](docs/excel-scenario-input.md) | Excel workbook contract, validation and demo scenarios |
| [`docs/application-workflow.md`](docs/application-workflow.md) | Current Streamlit workflow and results interface |
| [`docs/validation.md`](docs/validation.md) | Validation strategy and quality gates |
| [`docs/security-data-handling.md`](docs/security-data-handling.md) | Security and data-handling principles |
| [`docs/architecture-decisions.md`](docs/architecture-decisions.md) | Architectural decision index and rationale |

Recommended reading:

```text
README
  ↓
Getting Started
  ↓
Architecture
  ↓
Rules
  ↓
Reporting / Validation
  ↓
ADRs
```

---

## 🗺️ Roadmap

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
- [x] Excel scenario input\n- [x] Four-area executive narrative contract\n- [x] Ollama-compatible structured narrative parsing
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring/evaluation metrics
- [ ] Additional rule families and external data sources

---

## 👤 Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI
