# Credit Assessment System

> A modular credit assessment platform combining a deterministic rule engine, structured risk analysis, and optional LLM-assisted reporting.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.61.1-FF4B4B?logo=streamlit\&logoColor=white)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest\&logoColor=white)](https://pytest.org/)
[![Ruff](https://img.shields.io/badge/linting-Ruff-D7FF64)](https://docs.astral.sh/ruff/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

**Credit Assessment System** is a modular prototype for the assessment of corporate credit quality.

The system is designed around a strict architectural principle:

> **The deterministic rule engine is the source of truth. The LLM never makes the credit decision.**

The application separates the assessment process into two independent responsibilities:

1. **Credit assessment**
   Financial indicators are evaluated through deterministic business rules and explicit YAML configuration.

2. **Natural-language reporting**
   A deterministic generator or an optional LLM converts the already-computed assessment into an executive-level narrative.

This separation ensures that the introduction of generative AI does not compromise the reproducibility, traceability, or control of the underlying credit assessment.

The project can be used through both a **Python API** and an interactive **Streamlit application**.

---

## Key Features

* Deterministic, rule-based credit assessment
* Declarative rule configuration through YAML
* Explicit rule thresholds and severity policies
* Structured findings and risk factors
* `NORMAL`, `ATTENTION`, and `CRITICAL` assessment statuses
* `NOT_EVALUABLE` handling for missing or non-meaningful data
* Modular analysis and reporting agents
* LLM-assisted executive reporting
* Gemini and local Ollama integration
* Deterministic reporting fallback when an LLM is unavailable
* Provider-independent `LLMClient` abstraction
* Dependency injection and factory-based composition
* Extensive automated test suite with `pytest`
* Static analysis with Ruff
* Interactive Streamlit application
* Architecture designed for future REST/API and CI integration

---

## Architecture

The system follows a layered pipeline in which every stage has a clearly defined responsibility.

```text
                         ┌──────────────────────┐
                         │    CreditPosition    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │     AssessmentService     │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │        RuleEngine         │
                    └─────────────┬─────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
          R001                  R002                 R00N
       RuleResult            RuleResult           RuleResult
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────┐
              │   AssessmentStatusCalculator       │
              │   + CommentEngine                  │
              └──────────────────┬─────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
                    │         Assessment        │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │      AnalysisAgent        │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                  ┌──────────────────────────────┐
                  │      AssessmentAnalysis      │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
                    │      ReportingAgent       │
                    └─────────────┬─────────────┘
                                  │
                  ┌───────────────┴────────────────┐
                  │                                │
                  ▼                                ▼
       ┌──────────────────────┐        ┌────────────────────────┐
       │ LLMReportGenerator   │        │ DeterministicReport    │
       │                      │        │ Generator               │
       └──────────┬───────────┘        └────────────┬───────────┘
                  │                                 │
          ┌───────┼────────┐                        │
          ▼       ▼        ▼                        │
       Gemini  Ollama    Mock                       │
          │       │        │                        │
          └───────┴────────┴────────────┬───────────┘
                                        │
                                        ▼
                                ┌──────────────┐
                                │    Report    │
                                └──────────────┘
```

The complete workflow is coordinated by `AssessmentWorkflow` and exposed through `AssessmentOrchestrator`.

### Architectural boundary

The deterministic and generative layers are deliberately isolated.

The LLM is **not allowed** to:

* determine the assessment status;
* evaluate financial rules;
* modify rule thresholds;
* change rule severity;
* create or remove deterministic findings;
* modify limitations;
* invent financial figures;
* make an independent credit decision.

The LLM only generates the natural-language executive narrative from information that has already been deterministically assessed.

---

## Project Structure

```text
credit-assessment-system/
│
├── app/
│   ├── streamlit_app.py
│   └── ...                         # Modular Streamlit UI components
│
├── config/
│   └── rules.yaml                  # Declarative business-rule configuration
│
├── docs/
│   ├── architecture.md             # Architecture documentation
│   └── validation.md               # Validation and testing strategy
│
├── src/
│   ├── agents/
│   │   ├── base/
│   │   │   └── agent.py
│   │   ├── analysis/
│   │   │   └── analysis_agent.py
│   │   ├── reporting/
│   │   │   ├── report_generator.py
│   │   │   ├── deterministic_report_generator.py
│   │   │   ├── llm_report_generator.py
│   │   │   └── reporting_agent.py
│   │   └── workflow/
│   │       ├── assessment_workflow.py
│   │       └── workflow_factory.py
│   │
│   ├── comments/
│   │   ├── comment.py
│   │   ├── comment_engine.py
│   │   └── templates.py
│   │
│   ├── config/
│   │   ├── rule_configuration.py
│   │   └── rule_config_loader.py
│   │
│   ├── engine/
│   │   ├── rule_engine.py
│   │   └── finding_engine.py
│   │
│   ├── llm/
│   │   ├── client.py
│   │   ├── mock_client.py
│   │   ├── gemini_client.py
│   │   ├── ollama_client.py
│   │   ├── prompt_template.py
│   │   └── prompt_builder.py
│   │
│   ├── models/
│   │   ├── position.py
│   │   ├── assessment.py
│   │   ├── assessment_status.py
│   │   ├── assessment_analysis.py
│   │   ├── assessment_workflow.py
│   │   ├── analysis_finding.py
│   │   ├── rule_finding.py
│   │   └── report.py
│   │
│   ├── orchestration/
│   │   ├── orchestrator.py
│   │   └── orchestrator_factory.py
│   │
│   ├── rules/
│   │   ├── base/
│   │   ├── discovery.py
│   │   ├── registry.py
│   │   ├── result.py
│   │   ├── financial/
│   │   └── sustainability/
│   │
│   └── services/
│       ├── assessment_service.py
│       ├── assessment_status_calculator.py
│       └── service_factory.py
│
├── tests/
│   ├── conftest.py
│   ├── integration/
│   └── ...
│
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Deterministic Assessment Engine

The deterministic layer is the authoritative component of the system.

Each configured rule evaluates a `CreditPosition` and returns exactly one `RuleResult`.

### Assessment status

The current aggregation policy is intentionally simple and explicit:

| Triggered rules | Assessment status |
| --------------: | ----------------- |
|             `0` | `NORMAL`          |
|             `1` | `ATTENTION`       |
|            `2+` | `CRITICAL`        |

`NOT_EVALUABLE` results do **not** contribute to the triggered-rule count.

This guarantees that missing data does not automatically produce a negative credit assessment.

---

## Implemented Rules

The current configuration contains seven rules.

| Rule   | Indicator                       | Threshold | Direction       | Default severity |
| ------ | ------------------------------- | --------: | --------------- | ---------------- |
| `R001` | Revenue growth                  |    `-10%` | Lower is worse  | `MEDIUM`         |
| `R002` | EBITDA                          |       `0` | Lower is worse  | `HIGH`           |
| `R003` | EBITDA margin                   |      `0%` | Lower is worse  | `MEDIUM`         |
| `R004` | Net financial position / EBITDA |    `5.0x` | Higher is worse | `MEDIUM`         |
| `R005` | Interest expense / EBITDA       |   `0.60x` | Higher is worse | `MEDIUM`         |
| `R006` | Inventory contribution / EBITDA |   `0.30x` | Higher is worse | `MEDIUM`         |
| `R007` | Interest coverage ratio         |    `2.0x` | Lower is worse  | `MEDIUM`         |

Several rules support severity escalation through additional thresholds.

For example:

```yaml
rule_id: R004
rule_name: Net Financial Position / EBITDA
threshold: 5.0
severity: MEDIUM
severity_direction: HIGHER_IS_WORSE
severity_thresholds:
  - threshold: 7.0
    severity: HIGH
```

This allows the system to distinguish between a triggered condition and a more severe deterioration.

---

## Rule Configuration

Business parameters are externalized in:

```text
config/rules.yaml
```

This separation allows thresholds and severity policies to evolve without modifying the core `RuleEngine`.

Every rule configuration contains:

```yaml
rule_id:
rule_name:
category:
threshold:
severity:
severity_direction:
severity_thresholds:
```

The configuration loader validates the input and converts string values into strongly typed domain enums.

### Adding a new rule

A new rule can be introduced without changing the assessment, analysis, or reporting layers.

The process is:

1. Implement a new `Rule` subclass.
2. Register it with `@Rule.register("R00X")`.
3. Add its configuration to `config/rules.yaml`.
4. Optionally add a human-readable comment template.

The rule discovery mechanism automatically imports the rule modules and the registry instantiates the configured rules.

---

## Analysis Agent

`AnalysisAgent` transforms the deterministic `Assessment` into an `AssessmentAnalysis`.

It does not perform a second credit assessment.

The analysis layer produces:

* **Key findings** — triggered rule findings.
* **Risk factors** — high-severity findings.
* **Limitations** — rules that could not be evaluated.
* **Assessment status** — copied directly from the deterministic assessment.

The analysis therefore acts as a controlled boundary between decision logic and reporting.

---

## Reporting Layer

`ReportingAgent` provides a common interface for generating the final `Report`.

Two reporting strategies are supported.

### Deterministic reporting

`DeterministicReportGenerator` generates a report without any external dependency.

This is the default mode and guarantees:

* reproducible output;
* no network dependency;
* no API cost;
* deterministic behavior.

### LLM-assisted reporting

`LLMReportGenerator` uses the same deterministic `AssessmentAnalysis`, but delegates the generation of the executive narrative to an LLM.

The final report is constructed as follows:

```text
AssessmentAnalysis
       │
       ├── assessment_status ───────────────┐
       ├── key_findings ────────────────────┤
       ├── risk_factors ────────────────────┤
       └── limitations ─────────────────────┤
                                             ▼
                                      Final Report
                                             ▲
                                             │
                              LLM-generated narrative
```

The LLM therefore contributes only to the wording of the executive summary.

The deterministic findings, status, and limitations remain under application control.

---

## LLM Integration

The LLM layer is isolated behind:

```python
class LLMClient:
    def generate(self, prompt: str) -> str:
        ...
```

This allows different providers to be used without modifying the reporting architecture.

### Supported providers

| Client          | Purpose                              |
| --------------- | ------------------------------------ |
| `MockLLMClient` | Deterministic client used for tests  |
| `GeminiClient`  | Google Gemini API integration        |
| `OllamaClient`  | Local LLM integration through Ollama |

### Gemini

`GeminiClient` reads:

```text
GEMINI_API_KEY
```

from the environment when an API key is not supplied directly.

### Ollama

`OllamaClient` connects to a locally running Ollama instance.

The default endpoint is:

```text
http://localhost:11434
```

The model name must be explicitly supplied.

---

## Fault Isolation and Deterministic Fallback

The LLM is intentionally treated as an optional component.

When LLM-assisted reporting is enabled:

```text
LLMReportGenerator
        │
        │ success
        ▼
      Report
```

If the LLM fails because of an unavailable service, authentication problem, timeout, quota issue, network error, empty response, or other exception:

```text
LLMReportGenerator
        │
        │ failure
        ▼
DeterministicReportGenerator
        │
        ▼
      Report
```

This design guarantees that:

> **An LLM failure cannot invalidate the deterministic credit assessment.**

---

## Streamlit Application

The project includes an interactive Streamlit application located under:

```text
app/
```

The main entry point is:

```text
app/streamlit_app.py
```

The application is intentionally separated from the core domain logic.

The UI consumes the same orchestration and workflow components exposed by the Python backend, rather than implementing its own credit-assessment logic.

### Run the application

From the project root:

```bash
streamlit run app/streamlit_app.py
```

The Streamlit layer provides an interactive interface for running the credit assessment workflow and inspecting the generated assessment and reporting output.

The application can therefore be considered a presentation layer over:

```text
AssessmentOrchestrator
        │
        ▼
AssessmentWorkflow
        │
        ├── Assessment
        ├── Analysis
        └── Report
```

This separation keeps the UI replaceable without affecting the underlying domain model and deterministic engine.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
cd credit-assessment-system
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the tests

```bash
python -m pytest
```

### 5. Launch the Streamlit application

```bash
streamlit run app/streamlit_app.py
```

---

## Programmatic Usage

The system can also be consumed directly as a Python application.

```python
from src.models.position import CreditPosition
from src.orchestration.orchestrator_factory import create_default_orchestrator

orchestrator = create_default_orchestrator()

position = CreditPosition(
    position_id="ACME-2026",
    revenue_growth=-0.35,
    ebitda=-50_000,
    ebitda_margin=-0.05,
    nfp_to_ebitda=8.0,
    interest_expense=30_000,
)

report = orchestrator.run(position)

print(report.assessment_status)
print(report.executive_summary)

for group in report.findings_by_category:
    print(group.category)

print(report.limitations)
```

Because the default workflow is deterministic, the same input and rule configuration produce the same assessment.

---

## Enabling LLM-Assisted Reporting

LLM reporting is optional.

For Gemini:

```python
from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.orchestration.orchestrator import AssessmentOrchestrator
from src.llm.gemini_client import GeminiClient

llm_client = GeminiClient()

workflow = create_default_assessment_workflow(
    use_llm=True,
    llm_client=llm_client,
)

orchestrator = AssessmentOrchestrator(
    workflow=workflow,
)
```

The same workflow can be configured with:

* `GeminiClient`
* `OllamaClient`
* `MockLLMClient`

without changing the reporting architecture.

---

## Environment Configuration

The main environment variable currently used by the application is:

| Variable         | Description           |
| ---------------- | --------------------- |
| `GEMINI_API_KEY` | Google Gemini API key |

Example:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

On Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
```

Do not commit API keys or other secrets to the repository.

For local development, environment variables, Streamlit secrets, or other secure secret-management mechanisms should be used instead of hard-coding credentials.

---

## Testing

The project uses `pytest` for unit, integration, agent, workflow, and LLM abstraction tests.

Run the complete default suite:

```bash
python -m pytest
```

Run with coverage:

```bash
python -m pytest --cov=src --cov-report=term-missing
```

### Ollama tests

Tests that require a running Ollama instance are marked with:

```text
ollama
```

They are excluded from the default test run.

Run them explicitly with:

```bash
python -m pytest -m ollama
```

This keeps the standard test suite independent of external services.

---

## Code Quality

Static analysis is performed using Ruff.

```bash
python -m ruff check .
```

Type checking can be executed with:

```bash
python -m mypy src
```

The project therefore separates:

* automated behavioral validation with `pytest`;
* static analysis with `ruff`;
* optional static type checking with `mypy`.

---

## Design Principles

### Deterministic decision authority

The credit assessment is calculated exclusively by deterministic business rules.

### Separation of concerns

Assessment, analysis, reporting, UI, and LLM integration are separate architectural concerns.

### Traceability

A final finding can be traced through:

```text
Report
  ↓
AssessmentAnalysis
  ↓
Assessment
  ↓
RuleFinding
  ↓
RuleResult
  ↓
Rule
  ↓
Rule configuration
```

### Fail-safe reporting

LLM failures do not invalidate the deterministic assessment.

### Provider independence

The reporting layer depends on the `LLMClient` abstraction rather than a specific LLM vendor.

### Dependency injection

Services, workflows, agents, and clients receive their dependencies explicitly, improving testability and modularity.

### Configuration over hard-coded business logic

Thresholds and severity parameters are externalized in YAML rather than embedded in the orchestration layer.

---

## Security and Data Privacy

This project is intended for experimentation, demonstration, and academic development.

When integrating real financial data:

* avoid committing confidential or personally identifiable information;
* use anonymized or synthetic datasets whenever possible;
* never commit API credentials;
* carefully evaluate whether financial data may be sent to external LLM providers;
* apply appropriate organizational, regulatory, and security controls before using the architecture with production data.

The LLM layer should be considered an external processing component when a cloud provider such as Gemini is used.

For sensitive workloads, a local model through Ollama can provide an alternative deployment architecture, subject to the security and performance characteristics of the selected model and infrastructure.

---

## Limitations

The current implementation is a prototype and has several deliberate limitations.

### Assessment methodology

The current status aggregation is intentionally simple:

```text
0 triggered rules   → NORMAL
1 triggered rule    → ATTENTION
2+ triggered rules  → CRITICAL
```

It does not currently use severity-weighted, exposure-weighted, or category-weighted aggregation.

### Rule coverage

The current rule set contains seven financial indicators. Additional dimensions such as liquidity, collateral, cash flow, customer concentration, covenant structure, or sector-specific risk are not yet covered.

### LLM validation

LLM output validation currently focuses on response validity and architectural constraints rather than full semantic verification.

A stronger validation layer could detect:

* unsupported claims;
* numerical inconsistencies;
* contradictions with deterministic findings;
* missing risk factors;
* unsupported causal explanations.

### External LLM evaluation

The default automated test suite uses mocks and excludes tests requiring a running Ollama service.

Real provider behavior should therefore be evaluated separately through integration and human-in-the-loop testing.

### API layer

The current implementation is primarily exposed as a Python workflow and Streamlit application. A dedicated REST API layer is a potential future extension.

---

## Future Development

Planned or natural extensions include:

* additional financial and qualitative credit-risk rules;
* more advanced assessment aggregation policies;
* stronger semantic validation of LLM-generated narratives;
* structured LLM output;
* additional LLM providers;
* REST/FastAPI interface;
* containerized deployment;
* CI/CD with GitHub Actions;
* richer Streamlit dashboards;
* portfolio-level assessment;
* batch assessment of multiple positions;
* human-in-the-loop review workflows;
* audit logging and assessment versioning;
* systematic LLM quality, latency, and cost evaluation.

---

## Technology Stack

| Layer           | Technology                              |
| --------------- | --------------------------------------- |
| Language        | Python                                  |
| UI              | Streamlit                               |
| Configuration   | YAML                                    |
| Testing         | Pytest                                  |
| Static analysis | Ruff                                    |
| Type checking   | Mypy                                    |
| Cloud LLM       | Google Gemini                           |
| Local LLM       | Ollama                                  |
| Architecture    | Layered / modular / dependency-injected |

---

## License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the complete license text.

---

## Disclaimer

This project is a **prototype for educational, research, and demonstration purposes**.

It is not intended to replace professional credit analysis, internal banking procedures, regulatory requirements, model validation, risk governance, or human credit decisions.

The configured thresholds and assessment rules are implementation examples and should not be interpreted as generally applicable credit-risk policies.

---

## Author

Developed as a modular prototype exploring the combination of:

**deterministic credit-risk assessment + structured analysis + controlled LLM-assisted reporting.**
