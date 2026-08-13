# Credit Assessment System

A modular, rule-based credit assessment prototype with a multi-agent reporting layer and optional LLM-powered natural-language generation.

The system is designed around a clear separation of responsibilities:

> **Deterministic rules make the assessment. Agents structure and orchestrate the analysis. The LLM generates natural-language reporting.**

The LLM is therefore **not used as the credit decision engine**. Assessment status, triggered rules, severity and limitations are determined by the deterministic layer before any LLM is invoked.

---

## Overview

The system takes a structured `CreditPosition` and processes it through a deterministic assessment pipeline:

```text
Credit Position
      │
      ▼
Assessment Service
      │
      ▼
Rule Engine
      │
      ▼
Assessment
      │
      ▼
Analysis Agent
      │
      ▼
Assessment Analysis
      │
      ▼
Reporting Agent
      │
      ├─────────────────────────────┐
      │                             │
      ▼                             ▼
Deterministic Report          LLM Report Generator
Generator                           │
      │                             ▼
      │                         LLM Client
      │                             │
      │                        Gemini / Mock
      │                             │
      └──────────────┬──────────────┘
                     ▼
                   Report
```

The architecture supports both deterministic and LLM-based reporting while keeping the underlying credit assessment independent from the chosen reporting technology.

---

## Core Design Principles

### Deterministic Decision Layer

The credit assessment is produced entirely by explicit business rules.

The rule engine evaluates a `CreditPosition` and produces a collection of `RuleResult` objects containing:

* rule ID;
* rule name;
* category;
* evaluation status;
* calculated value;
* threshold;
* severity.

A simplified flow is:

```text
CreditPosition
      ↓
Individual Rules
      ↓
RuleResult[]
      ↓
Assessment Status
      ↓
Assessment
```

The available rule statuses distinguish between different evaluation outcomes:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

This allows the system to distinguish an actual risk signal from an indicator that could not be evaluated.

### Explicit Severity

Triggered rules are associated with an explicit severity:

```text
LOW
MEDIUM
HIGH
```

The deterministic analysis layer uses these results to construct the structured `AssessmentAnalysis`.

For example:

```text
Triggered rules
      │
      ├── all triggered rules → key findings
      │
      └── HIGH severity rules → risk factors

Not evaluable rules → limitations
```

### Separation of Decision and Generation

The LLM receives the structured result of the deterministic analysis.

It does **not** receive authority to:

* calculate the assessment status;
* change the assessment status;
* determine which rules were triggered;
* modify rule severity;
* create new credit-risk indicators;
* alter structured findings or limitations.

The LLM is used for natural-language reporting only.

---

# Architecture

## Project Structure

```text
src/
├── agents/
│   ├── analysis/
│   │   └── analysis_agent.py
│   ├── base/
│   │   └── agent.py
│   ├── reporting/
│   │   ├── deterministic_report_generator.py
│   │   ├── llm_report_generator.py
│   │   ├── report_generator.py
│   │   └── reporting_agent.py
│   └── workflow/
│       ├── assessment_workflow.py
│       └── workflow_factory.py
│
├── comments/
│   ├── comment.py
│   ├── comment_engine.py
│   └── templates.py
│
├── config/
│   ├── rule_config_loader.py
│   └── rule_configuration.py
│
├── engine/
│   └── rule_engine.py
│
├── llm/
│   ├── client.py
│   ├── mock_client.py
│   └── gemini_client.py
│
├── models/
│   ├── assessment.py
│   ├── assessment_analysis.py
│   ├── assessment_status.py
│   ├── assessment_workflow.py
│   ├── position.py
│   └── report.py
│
├── orchestration/
│   ├── orchestrator.py
│   └── orchestrator_factory.py
│
├── rules/
│   ├── base/
│   ├── financial/
│   ├── sustainability/
│   ├── discovery.py
│   ├── registry.py
│   └── result.py
│
└── services/
    ├── assessment_service.py
    ├── assessment_status_calculator.py
    └── service_factory.py
```

The repository also contains a `tests/` hierarchy mirroring the main application components and a `scripts/` directory for manual integration checks such as real Gemini execution.

---

# Deterministic Assessment Layer

## Rule Engine

The `RuleEngine` is responsible for executing the registered credit rules against a `CreditPosition`.

Rules are implemented as independent classes and share a common `Rule` abstraction.

A rule produces a `RuleResult`:

```python
RuleResult(
    rule_id=...,
    rule_name=...,
    category=...,
    status=...,
    value=...,
    threshold=...,
    severity=...,
)
```

This makes the decision process explicit and traceable.

### Rule Registration

Rules are registered through the base rule infrastructure, allowing the engine to discover and execute rules without hard-coding every rule into the engine itself.

Current examples include financial and sustainability indicators such as:

```text
Revenue Growth
Negative EBITDA
EBITDA Margin
PFN / EBITDA
Interest Coverage Ratio
Financial Expenses / EBITDA
EBITDA Inventory Contribution
```

The rule catalog can be extended without changing the overall assessment architecture.

---

# Assessment Service

The `AssessmentService` coordinates deterministic assessment execution.

Conceptually:

```text
CreditPosition
      ↓
RuleEngine
      ↓
RuleResult[]
      ↓
AssessmentStatusCalculator
      ↓
Assessment
```

The resulting `Assessment` contains the deterministic status and rule-level results.

The status is therefore established **before the LLM layer is involved**.

---

# Multi-Agent Layer

The project intentionally uses a small number of agents with clearly separated responsibilities.

## Analysis Agent

The `AnalysisAgent` transforms the deterministic `Assessment` into an `AssessmentAnalysis`.

```text
Assessment
    ↓
AnalysisAgent
    ↓
AssessmentAnalysis
```

`AssessmentAnalysis` contains:

```text
position_id
assessment_status
key_findings
risk_factors
limitations
```

The current logic is deterministic:

* all triggered rules become key findings;
* high-severity triggered rules become risk factors;
* non-evaluable rules become limitations.

The agent does not call an LLM.

This is intentional: the analytical structure remains deterministic and auditable.

---

## Reporting Agent

The `ReportingAgent` is responsible for report generation.

It depends on the abstract `ReportGenerator` interface rather than on a specific implementation.

```text
ReportingAgent
      ↓
ReportGenerator
```

Two implementations are currently available:

```text
ReportGenerator
      │
      ├── DeterministicReportGenerator
      │
      └── LLMReportGenerator
```

This allows the reporting strategy to be changed without modifying the agent itself.

---

# Deterministic Reporting

`DeterministicReportGenerator` provides a non-LLM reporting strategy.

It generates the executive summary directly from the `AssessmentAnalysis`.

For example:

```text
NORMAL    → "The credit assessment is classified as normal."
ATTENTION → "The credit assessment requires attention."
CRITICAL  → "The credit assessment is classified as critical."
```

Structured findings and limitations are copied directly from the analysis.

This implementation provides a deterministic baseline against which LLM-generated reporting can be compared.

---

# LLM Reporting

## LLM Report Generator

`LLMReportGenerator` uses an injected `LLMClient` to generate the executive summary.

```text
AssessmentAnalysis
      ↓
LLMReportGenerator
      ↓
_build_prompt()
      ↓
LLMClient.generate()
      ↓
Generated executive summary
      ↓
Report
```

The LLM receives:

```text
Assessment Status
Key Findings
Risk Factors
Limitations
```

and is instructed to generate a concise, professional credit-assessment summary.

The prompt explicitly constrains the model to:

* use only the provided assessment information;
* avoid inventing financial data;
* avoid inventing causes or trends;
* avoid modifying the assessment status;
* avoid making the credit decision;
* avoid unsupported recommendations;
* distinguish findings from limitations.

---

# LLM Abstraction

The LLM layer is provider-independent through the `LLMClient` abstraction:

```python
class LLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...
```

The current implementations include:

```text
LLMClient
    │
    ├── MockLLMClient
    │
    └── GeminiClient
```

This provides dependency inversion between the reporting layer and the underlying model provider.

The reporting agent therefore does not depend directly on Gemini.

---

# Gemini Integration

`GeminiClient` provides the real LLM implementation using the Google Gemini API.

The API key is supplied through the environment rather than stored in the repository.

On Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

For a local real-LLM check:

```powershell
python -m scripts.check_gemini_workflow
```

The repository does not require Gemini access for the normal automated test suite.

---

# LLM Failure and Deterministic Fallback

The reporting layer includes a deterministic fallback.

When the LLM reporting path fails, the `ReportingAgent` can fall back to `DeterministicReportGenerator`.

```text
LLMReportGenerator
       │
       ├── success ────────────────► LLM Report
       │
       └── failure
             │
             ▼
DeterministicReportGenerator
             │
             ▼
     Deterministic Report
```

This ensures that:

> **LLM availability is not a prerequisite for deterministic credit assessment.**

A model failure therefore affects the reporting mechanism, not the underlying assessment.

---

# Output Validation

The `LLMReportGenerator` treats LLM output as untrusted generated content.

The current validation layer checks that:

1. the response is not empty;
2. the generated text contains the deterministic assessment status.

Structured report fields are not taken from the LLM response.

Instead:

```python
Report(
    position_id=analysis.position_id,
    assessment_status=analysis.assessment_status,
    executive_summary=response,
    findings=analysis.key_findings,
    limitations=analysis.limitations,
)
```

Therefore the LLM controls only the natural-language `executive_summary`.

The structured assessment remains authoritative.

---

# Workflow and Orchestration

The workflow coordinates the main application stages:

```text
AssessmentService
      ↓
AnalysisAgent
      ↓
ReportingAgent
```

The orchestration layer provides the top-level entry point for the complete assessment process.

The workflow factory supports deterministic and LLM reporting through dependency injection.

Conceptually:

```python
create_default_assessment_workflow(
    use_llm=False,
)
```

uses the deterministic generator.

```python
create_default_assessment_workflow(
    use_llm=True,
    llm_client=MockLLMClient(),
)
```

uses the LLM reporting path in automated tests.

A real Gemini workflow can be executed by supplying:

```python
GeminiClient()
```

as the `LLMClient`.

---

# Testing Strategy

The project follows a test-first and layered testing approach.

## Automated Tests

The automated test suite covers:

```text
Rules
Rule Engine
Configuration
Services
Models
Analysis Agent
Reporting Agent
Report Generators
LLM Abstraction
Workflow
Orchestration
Integration
```

The LLM-related tests use `MockLLMClient`, which keeps automated testing:

* deterministic;
* fast;
* independent of external APIs;
* free of API costs;
* suitable for CI/CD execution.

The current test suite contains **151+ automated tests**, all passing at the current development checkpoint.

Run the complete suite with:

```powershell
python -m pytest
```

---

## Static Analysis

The project uses Ruff for linting:

```powershell
python -m ruff check .
```

The CI pipeline executes the same quality checks used during local development.

---

## Coverage

Coverage is enforced in CI with:

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

This keeps the deterministic application code and supporting infrastructure covered by automated tests.

---

# Real LLM Checks

Real Gemini calls are deliberately separated from the normal pytest suite.

Manual integration checks are located under:

```text
scripts/
```

For example:

```powershell
python -m scripts.check_gemini_workflow
```

These checks allow the project to validate real model behavior while keeping the automated test suite independent from external services.

The real Gemini workflow has been evaluated on multiple deterministic assessment scenarios, including:

```text
CRITICAL
ATTENTION
NORMAL
```

The observed behavior confirms that the generated reports preserve the deterministic assessment status and distinguish findings, risk factors and limitations.

---

# Example End-to-End Flow

A typical assessment follows this sequence:

```text
1. CreditPosition
       ↓
2. AssessmentService
       ↓
3. RuleEngine
       ↓
4. RuleResult[]
       ↓
5. AssessmentStatusCalculator
       ↓
6. Assessment
       ↓
7. AnalysisAgent
       ↓
8. AssessmentAnalysis
       ↓
9. ReportingAgent
       ↓
10. ReportGenerator
       ↓
11. Deterministic or LLM reporting
       ↓
12. Report
```

With the LLM enabled:

```text
AssessmentAnalysis
       ↓
LLMReportGenerator
       ↓
Prompt
       ↓
GeminiClient
       ↓
Gemini
       ↓
Executive Summary
       ↓
Report
```

---

# Why This Architecture?

The architecture is deliberately designed around a **bounded role for generative AI**.

The deterministic layer is responsible for:

```text
Business rules
Thresholds
Rule evaluation
Severity
Assessment status
Structured findings
Structured risk factors
Limitations
```

The agent layer is responsible for:

```text
Analysis structuring
Workflow coordination
Report generation
```

The LLM layer is responsible for:

```text
Natural-language generation
```

This creates a clear separation between:

> **Decision Logic** and **Language Generation**

The approach is intended to improve:

* traceability;
* explainability;
* testability;
* reproducibility;
* provider independence;
* resilience to LLM failures.

---

# Current Status

The current prototype includes:

```text
✓ Rule-based credit assessment engine
✓ Configurable rule discovery and registry
✓ Explicit rule severity and status
✓ Assessment service
✓ Analysis Agent
✓ Reporting Agent
✓ Deterministic report generation
✓ LLM report generation
✓ Provider-independent LLM interface
✓ Mock LLM implementation
✓ Gemini implementation
✓ Prompt constraints
✓ LLM response validation
✓ Deterministic reporting fallback
✓ End-to-end workflow
✓ Real Gemini integration checks
✓ Automated test suite
✓ Ruff linting
✓ GitHub Actions CI
```

---

# Future Development

Potential future extensions include:

* richer structured analysis outputs;
* stronger evaluation of LLM faithfulness;
* automated comparison between deterministic and LLM-generated reports;
* additional LLM providers;
* more sophisticated report templates;
* structured LLM outputs;
* evaluation metrics for reporting quality;
* further orchestration of specialized analytical workflows.

These extensions can be added without changing the deterministic decision layer.

---

# Key Architectural Principle

The central principle of the project is:

```text
        DETERMINISTIC LAYER
        ───────────────────
        Rules determine.
        Agents structure.
                │
                ▼
        GENERATIVE LAYER
        ─────────────────
        LLM communicates.
```

The system is therefore **LLM-assisted rather than LLM-driven**: the model enhances the communication of an assessment that has already been determined by an explicit and traceable rule engine.
