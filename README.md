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

The Streamlit application supports two input sources:

- **Demo Scenario** — the built-in synthetic demonstration case.
- **Excel Upload** — an `.xlsx` workbook containing one or more structured assessment scenarios.

For Excel input, `Credit_Position` is mandatory. `Customer_Profile`, `Behavioural` and `Debt_Sustainability` are optional domain sheets. Each domain sheet uses a shared `scenario_id` to identify the same case across domains.

The repository includes the reference workbook `examples/excel/demo_scenarios.xlsx`. It contains a documentation-only `README` sheet plus the four loader-compatible domain sheets. The three synthetic scenarios are:

| Scenario | Purpose |
|---|---|
| `DEMO-NORMAL` | baseline case with no significant financial triggers |
| `DEMO-ATTENTION` | isolated MEDIUM financial deterioration |
| `DEMO-CRITICAL` | multiple HIGH financial deterioration indicators |

Customer Profile and Behavioural inputs are deliberately kept stable across the three scenarios so that the main differences are attributable to the financial inputs. The workbook is formatted as a user-facing demonstration artifact while preserving the loader contract.

See [`docs/excel-scenario-input.md`](docs/excel-scenario-input.md) for the complete workbook contract and validation behaviour.

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

Customer Profile is treated as a **contextual information layer**, not merely as a list of deterministic risk rules. It combines descriptive customer information, risk-profile evolution, statistical predictiveness, relationship context and relevant historical events.

The profile is organised into four reporting sections:

1. **General Information** — identity, counterparty type, business activity and operating context.
2. **Risk Profile & Predictiveness** — EWS score information, active EWIs, rating/PD information and risk-grade evolution.
3. **Relationship & Counterparty Context** — banking relationship, ownership/management and counterparty-specific context.
4. **Relevant Events** — protests, bankruptcies, litigation and significant historical events.

The distinction between **contextual profile information** and **deterministic rule evidence** is intentional:

- deterministic customer-profile rules produce authoritative `RuleResult` objects and can affect section status;
- descriptive profile fields provide context and do not automatically become pseudo-rules;
- the Executive Summary receives only the contextual information selected as material by the deterministic `CustomerProfileMaterialityPolicy`;
- profile facts already represented by deterministic Customer Profile rules are excluded from that contextual subset;
- the reporting paths merge rule evidence and material context into a single `Customer Profile` Executive Narrative section;
- the LLM receives that already-selected material context and may only verbalise it.

This prevents the Executive Summary from becoming either a dump of all available customer data, a duplicate of rule evidence, or a second decision engine.

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

The README deliberately does **not** maintain a duplicated list of rule IDs, rule counts or thresholds. Those are catalogue data and can evolve independently of the architecture.

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
pip install -r requirements.txt
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
- [x] Excel scenario input
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring/evaluation metrics
- [ ] Additional rule families and external data sources

---

## 👤 Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI
