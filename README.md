# Credit Assessment System

A modular, rule-based credit assessment prototype with a multi-agent workflow and optional LLM-powered reporting layer.

The system is designed around a strict separation between **credit decision logic** and **natural-language generation**:

> **Deterministic rules determine the assessment. Agents structure and orchestrate the analysis. The LLM supports natural-language reporting.**

The LLM is therefore **not part of the credit decision-making process**. Assessment status, rule outcomes, severity, findings, risk factors, and limitations are established by the deterministic layer before the reporting stage.

This architecture is intended to provide a balance between:

* deterministic and auditable decision logic;
* modular software architecture;
* structured analysis;
* controlled use of generative AI;
* testability and reproducibility;
* resilience to external LLM failures.

---

# 1. Project Overview

The `credit-assessment-system` is a prototype designed to demonstrate how a traditional rule-based credit assessment process can be combined with a modular multi-agent architecture and a constrained LLM reporting component.

The system processes a structured `CreditPosition` through three principal stages:

```text
                    CREDIT ASSESSMENT WORKFLOW

CreditPosition
      │
      ▼
Assessment Service
      │
      ▼
Deterministic Rule Engine
      │
      ▼
Assessment
      │
      ▼
Analysis Agent
      │
      ▼
AssessmentAnalysis
      │
      ▼
Reporting Agent
      │
      ├──────────────────────────────┐
      │                              │
      ▼                              ▼
Deterministic Report          LLM Report Generator
Generator                           │
      │                             ▼
      │                         LLM Client
      │                             │
      │                     ┌───────┴───────┐
      │                     ▼               ▼
      │                  Gemini           Mock
      │                     │
      └──────────────┬──────┘
                     ▼
                   Report
```

The reporting mechanism can therefore be changed without changing the underlying credit assessment logic.

---

# 2. Architectural Principles

The architecture is based on several fundamental principles.

## 2.1 Deterministic Decision-Making

The credit assessment is determined exclusively by explicit business rules.

The deterministic layer is responsible for:

* rule evaluation;
* threshold evaluation;
* severity assignment;
* assessment status;
* structured findings;
* risk factors;
* limitations.

The LLM cannot modify any of these elements.

---

## 2.2 Separation of Decision and Reporting

The system explicitly separates:

```text
Decision Logic
      │
      ▼
Deterministic
      │
      ▼
Assessment
      │
      ▼
Structured Analysis
      │
      ▼
Reporting
      │
      ├── Deterministic
      └── LLM-based
```

This means that the reporting technology can evolve independently from the credit assessment engine.

---

## 2.3 Controlled Use of Generative AI

The LLM is deliberately restricted to the reporting layer.

It is not used to:

* determine the assessment status;
* evaluate business rules;
* select thresholds;
* determine severity;
* create new findings;
* modify existing findings;
* modify limitations;
* make independent credit decisions.

Its role is limited to transforming already-validated structured information into natural-language reporting.

---

## 2.4 Explicit Data Contracts

Each major processing stage communicates through structured domain objects:

```text
CreditPosition
      ↓
Assessment
      ↓
AssessmentAnalysis
      ↓
Report
```

This makes intermediate results explicit, observable, and independently testable.

---

## 2.5 Provider Independence

The reporting layer depends on abstractions rather than on a specific LLM provider.

The current implementation supports:

```text
LLMClient
    ├── MockLLMClient
    └── GeminiClient
```

This allows the underlying provider to be replaced without modifying the reporting architecture.

---

## 2.6 Resilience

The availability of an external LLM service must not determine whether the deterministic assessment can be completed.

The reporting layer therefore provides a deterministic fallback:

```text
LLM Report Generator
        │
        ├── success ───────► LLM Report
        │
        └── failure
                │
                ▼
        Deterministic Report
```

Consequently:

> **LLM availability is not a prerequisite for credit assessment.**

---

# 3. System Architecture

The system is organized into four principal logical layers.

```text
┌───────────────────────────────────────────────────────┐
│                   ORCHESTRATION                       │
│                                                       │
│              Orchestrator / Workflow                 │
└──────────────────────────┬────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────┐
│                    ASSESSMENT                          │
│                                                       │
│ Assessment Service → Rule Engine → Rules              │
└──────────────────────────┬────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────┐
│                      ANALYSIS                          │
│                                                       │
│                  Analysis Agent                       │
└──────────────────────────┬────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────┐
│                     REPORTING                          │
│                                                       │
│ Reporting Agent → Deterministic / LLM Generator       │
└──────────────────────────┬────────────────────────────┘
                           │
                           ▼
                         Report
```

The detailed architectural description is available in [`docs/architecture.md`](docs/architecture.md).

---

# 4. Project Structure

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

tests/
├── unit/
├── integration/
└── ...

scripts/
└── check_gemini_workflow.py
```

The repository structure follows the same separation of responsibilities as the runtime architecture.

---

# 5. Deterministic Assessment Layer

The deterministic assessment layer is the **authoritative decision-making component** of the system.

Its primary components are:

* `CreditPosition`;
* assessment rules;
* `RuleEngine`;
* `AssessmentService`;
* `AssessmentStatusCalculator`;
* `Assessment`.

---

## 5.1 Credit Position

`CreditPosition` represents the structured financial information associated with a credit position.

Current indicators include, among others:

* revenue growth;
* EBITDA;
* profit/loss;
* EBITDA margin;
* PFN-to-EBITDA;
* interest expense.

The system intentionally operates on structured domain data rather than natural-language input.

This ensures that rule evaluation is deterministic and reproducible.

---

## 5.2 Rule Engine

The `RuleEngine` executes the registered rules against a `CreditPosition`.

Rules are implemented independently and share a common rule abstraction.

Each rule produces a structured `RuleResult` containing information such as:

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

This makes every rule evaluation explicit and traceable.

### Rule Status

The system distinguishes between:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

This distinction is important because an unavailable or non-evaluable indicator must not automatically be interpreted as either a positive or negative signal.

---

## 5.3 Rule Severity

Triggered rules can be associated with explicit severity levels:

```text
LOW
MEDIUM
HIGH
```

Severity is determined by the deterministic rule configuration and is not delegated to the LLM.

---

## 5.4 Rule Configuration

Rule-specific configuration is separated from rule execution.

Configuration can define elements such as:

* rule identifier;
* rule name;
* category;
* threshold;
* severity;
* severity direction;
* severity thresholds.

This allows rule behavior to be configured without embedding all business parameters directly inside the rule implementation.

---

## 5.5 Assessment Service

The `AssessmentService` coordinates the deterministic assessment process:

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

The service is responsible for coordinating rule execution and producing the final deterministic assessment.

The assessment status is therefore established before the LLM reporting layer is invoked.

---

# 6. Analysis Layer

The analysis layer transforms the deterministic `Assessment` into an `AssessmentAnalysis`.

```text
Assessment
    │
    ▼
AnalysisAgent
    │
    ▼
AssessmentAnalysis
```

The `AnalysisAgent` does not perform a second independent assessment.

Instead, it structures the deterministic results for downstream reporting.

The resulting object contains:

```text
position_id
assessment_status
key_findings
risk_factors
limitations
```

The current deterministic mapping is:

```text
Triggered rules
      ├──► Key Findings
      │
      └──► High-severity findings → Risk Factors

Not-evaluable rules
      └──► Limitations
```

This ensures that the analytical representation remains consistent with the underlying assessment.

---

# 7. Reporting Layer

The reporting layer converts `AssessmentAnalysis` into a final `Report`.

The main component is the `ReportingAgent`.

It depends on the abstract `ReportGenerator` interface:

```text
ReportingAgent
      │
      ▼
ReportGenerator
      │
      ├── DeterministicReportGenerator
      │
      └── LLMReportGenerator
```

This design allows reporting strategies to be replaced without modifying the orchestration or assessment layers.

---

## 7.1 Deterministic Reporting

`DeterministicReportGenerator` provides a completely deterministic reporting implementation.

The executive summary is generated from the assessment status, while structured findings and limitations are preserved from the analysis.

For example:

```text
NORMAL
    ↓
"The credit assessment is classified as normal."

ATTENTION
    ↓
"The credit assessment requires attention."

CRITICAL
    ↓
"The credit assessment is classified as critical."
```

This implementation serves two purposes:

1. it provides a reliable reporting mechanism;
2. it provides a deterministic baseline against which LLM-generated reporting can be evaluated.

---

## 7.2 LLM Reporting

`LLMReportGenerator` uses an injected `LLMClient` to generate the executive summary.

The processing flow is:

```text
AssessmentAnalysis
      ↓
LLMReportGenerator
      ↓
Prompt Construction
      ↓
LLMClient.generate()
      ↓
Response Validation
      ↓
Report
```

The model receives structured information including:

* assessment status;
* key findings;
* risk factors;
* limitations.

The generated text is therefore grounded in the deterministic analysis.

---

# 8. LLM Integration

The LLM layer is isolated behind the `LLMClient` abstraction.

```text
LLMReportGenerator
        │
        ▼
    LLMClient
        │
        ├── MockLLMClient
        │
        └── GeminiClient
```

## 8.1 `LLMClient`

The abstraction defines the interface required by the reporting layer:

```python
class LLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...
```

The reporting layer therefore does not depend directly on Gemini or any other model provider.

---

## 8.2 `MockLLMClient`

`MockLLMClient` is used by the automated test suite.

It provides deterministic responses without external API calls.

This keeps automated tests:

* reproducible;
* fast;
* independent of network availability;
* independent of external model behavior;
* free from API costs.

---

## 8.3 `GeminiClient`

`GeminiClient` provides the production-style integration with the Google Gemini API.

The API credential is supplied through an environment variable and is not stored in the repository.

For example, in PowerShell:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

A manual real-LLM workflow can then be executed with:

```powershell
python -m scripts.check_gemini_workflow
```

Real LLM calls are intentionally separated from the automated test suite.

---

# 9. LLM Response Validation

LLM output is treated as **untrusted generated content**.

Before the response is accepted, it is validated against the deterministic assessment context.

The current validation process verifies, at minimum:

1. the response is not empty;
2. the expected deterministic assessment status is present.

Depending on the reporting contract, additional content validation can be applied to ensure that required findings and risk factors are represented.

The important architectural property is that structured assessment information is **not reconstructed from the LLM response**.

The final report is assembled using the deterministic analysis:

```python
Report(
    position_id=analysis.position_id,
    assessment_status=analysis.assessment_status,
    executive_summary=response,
    findings=analysis.key_findings,
    limitations=analysis.limitations,
)
```

Therefore:

```text
LLM controls:
    executive_summary

Deterministic layer controls:
    assessment_status
    findings
    risk_factors
    limitations
```

This is one of the principal safeguards of the architecture.

---

# 10. Failure Handling and Fallback

The reporting architecture uses a primary/fallback strategy.

```text
                    ReportingAgent
                          │
                          ▼
                 LLMReportGenerator
                          │
                    success / failure
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
        LLM Report              Deterministic
                                Report Generator
             │                         │
             └────────────┬────────────┘
                          ▼
                        Report
```

Failures may include:

* external service unavailability;
* client exceptions;
* invalid responses;
* empty responses;
* failed response validation.

When the LLM path fails, the deterministic generator can produce the final report.

The fallback does not recalculate the assessment. It consumes the same deterministic `AssessmentAnalysis`.

Therefore:

```text
LLM failure
     ≠
Assessment failure
```

The failure is isolated to the generative reporting component.

---

# 11. Workflow and Orchestration

The `AssessmentWorkflow` coordinates the three principal stages:

```text
Assessment
    ↓
Analysis
    ↓
Reporting
```

A complete execution can be represented as:

```text
CreditPosition
      ↓
AssessmentService.assess()
      ↓
Assessment
      ↓
AnalysisAgent.run()
      ↓
AssessmentAnalysis
      ↓
ReportingAgent.run()
      ↓
Report
```

The workflow returns an `AssessmentWorkflowResult` containing:

* `assessment`;
* `analysis`;
* `report`.

The `Orchestrator` provides the application-level entry point for executing the workflow.

Factories are used to assemble the default application configuration and inject the required dependencies.

---

# 12. Testing Strategy

The project follows a layered testing strategy.

```text
Unit Tests
    ↓
Integration Tests
    ↓
End-to-End Tests
    ↓
Real LLM Validation
```

Each level addresses a different aspect of system correctness.

---

## 12.1 Unit Testing

Unit tests cover the behavior of individual components, including:

* domain models;
* rules;
* rule configuration;
* rule discovery;
* rule registry;
* rule engine;
* assessment services;
* status calculation;
* analysis agent;
* reporting agent;
* report generators;
* LLM abstraction;
* mock LLM client.

---

## 12.2 Integration Testing

Integration tests verify the interaction between components such as:

* assessment service and rule engine;
* assessment and analysis;
* analysis and reporting;
* LLM reporting and response validation;
* workflow construction;
* fallback behavior.

---

## 12.3 End-to-End Testing

End-to-end tests execute the complete pipeline from `CreditPosition` to `Report`.

They verify key architectural invariants, including:

```text
Assessment.status
        =
AssessmentAnalysis.assessment_status
        =
Report.assessment_status
```

They also verify that deterministic findings and limitations propagate correctly through the workflow.

---

## 12.4 LLM Testing

Automated LLM tests use `MockLLMClient`.

Dedicated tests verify scenarios such as:

* valid LLM response;
* empty response;
* missing assessment status;
* LLM exception;
* deterministic fallback;
* preservation of deterministic findings;
* preservation of limitations.

Real Gemini execution is tested separately to avoid making CI dependent on an external service.

---

# 13. Quality Assurance

## Automated Tests

Run the complete test suite with:

```powershell
python -m pytest
```

The repository contains an extensive automated test suite covering the deterministic assessment engine, agents, reporting layer, LLM abstractions, workflow, and integration behavior.

The exact test count may evolve as the project develops.

---

## Static Analysis

Ruff is used for static analysis and linting:

```powershell
python -m ruff check .
```

The same quality checks are executed in CI.

---

## Test Coverage

Coverage can be evaluated with:

```powershell
python -m pytest --cov=src --cov-report=term-missing
```

The CI pipeline enforces the configured coverage threshold.

---

# 14. Continuous Integration

The project uses GitHub Actions to automate quality checks.

The CI pipeline is designed to verify that changes preserve the expected software quality before they are integrated into the main development branch.

The CI process includes automated testing and static analysis.

This provides an additional safeguard against regressions in the deterministic assessment and reporting layers.

---

# 15. Real LLM Validation

Real Gemini calls are intentionally separated from the automated test suite.

Manual integration checks are available under:

```text
scripts/
```

For example:

```powershell
python -m scripts.check_gemini_workflow
```

Scenario-based validation covers representative deterministic assessment outcomes:

```text
NORMAL
ATTENTION
CRITICAL
```

The purpose of these executions is not to replace deterministic automated tests, but to validate the behavior of the complete system when connected to an actual LLM service.

The real-LLM validation focuses on:

* preservation of the deterministic assessment status;
* consistency of generated reporting;
* adherence to the supplied findings;
* treatment of risk factors;
* treatment of limitations;
* behavior of the reporting layer across different assessment scenarios.

---

# 16. Example End-to-End Execution

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
11. Deterministic or LLM Reporting
        ↓
12. Report
```

With LLM reporting enabled:

```text
AssessmentAnalysis
        ↓
LLMReportGenerator
        ↓
Prompt Construction
        ↓
GeminiClient
        ↓
Gemini API
        ↓
Generated Executive Summary
        ↓
Response Validation
        ↓
Report
```

The deterministic assessment is completed before the LLM is invoked.

---

# 17. Architectural Guarantees

The architecture is designed to enforce the following invariants.

### Assessment Authority

```text
Assessment.status
```

is determined exclusively by the deterministic assessment layer.

### Status Preservation

```text
Assessment.status
    =
AssessmentAnalysis.assessment_status
    =
Report.assessment_status
```

### Finding Preservation

Structured findings originate from the deterministic assessment pipeline and are not reconstructed from LLM output.

### Limitation Preservation

Limitations identified by the deterministic analysis are preserved independently of the generated executive summary.

### LLM Isolation

An LLM failure cannot change the deterministic assessment.

### Reporting Substitutability

The reporting layer can switch between:

```text
LLMReportGenerator
```

and

```text
DeterministicReportGenerator
```

without modifying the deterministic assessment engine.

These invariants represent the principal architectural safeguards of the system.

---

# 18. Current Scope

The current prototype focuses on the core software architecture required to demonstrate:

* deterministic credit assessment;
* configurable business rules;
* explicit severity and status;
* structured analysis;
* modular report generation;
* controlled LLM integration;
* LLM response validation;
* deterministic fallback;
* end-to-end orchestration;
* automated testing;
* real LLM integration checks;
* continuous integration.

The prototype does not currently require infrastructure such as:

* relational or NoSQL databases;
* REST APIs;
* web frontends;
* message queues;
* distributed services;
* Kubernetes;
* Terraform;
* vector databases;
* retrieval-augmented generation.

These technologies can be introduced in future iterations if justified by additional functional or deployment requirements.

---

# 19. Current Status

The current implementation includes:

```text
✓ Deterministic rule-based assessment engine
✓ Configurable rule discovery and registry
✓ Explicit rule status
✓ Explicit rule severity
✓ Configurable severity thresholds
✓ Assessment service
✓ Assessment status calculation
✓ Analysis Agent
✓ Reporting Agent
✓ Deterministic report generation
✓ LLM report generation
✓ Provider-independent LLM abstraction
✓ Mock LLM implementation
✓ Gemini integration
✓ Controlled prompt construction
✓ LLM response validation
✓ Deterministic fallback
✓ End-to-end workflow
✓ Application-level orchestration
✓ Automated testing
✓ Ruff static analysis
✓ GitHub Actions CI
✓ Real Gemini integration checks
```

---

# 20. Documentation

The repository documentation is organized around the main architectural and validation aspects of the project.

| Document               | Purpose                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `README.md`            | Project overview, architecture, usage, testing, and current status |
| `docs/architecture.md` | Detailed architectural description and design rationale            |
| `docs/validation.md`   | Validation strategy, test levels, scenarios, and limitations       |

This separation keeps the README focused on the project as a whole while allowing the architecture and validation documents to provide greater technical depth.

---

# 21. Future Development

Potential future extensions include:

* richer structured analysis outputs;
* stronger automated evaluation of LLM faithfulness;
* systematic comparison between deterministic and LLM-generated reports;
* additional LLM providers;
* structured LLM outputs;
* improved prompt and response validation;
* human evaluation of report quality;
* reporting-quality metrics;
* latency and cost analysis;
* broader scenario-based validation;
* API and web application layers;
* persistent assessment storage.

These extensions can be introduced while preserving the deterministic assessment boundary.

---

# 22. Core Architectural Principle

The central principle of the project can be summarized as:

```text
             DETERMINISTIC LAYER
             ───────────────────
             Rules determine.
             Agents structure.
                    │
                    ▼
              REPORTING LAYER
             ───────────────────
             LLM communicates.
```

Or, more simply:

> **The system is LLM-assisted, not LLM-driven.**

The deterministic assessment engine remains the source of truth, while the agent and LLM layers are responsible for structuring and communicating an assessment that has already been determined through explicit and traceable rules.

This boundary is the central architectural decision of the `credit-assessment-system`.
