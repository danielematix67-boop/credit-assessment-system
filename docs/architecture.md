# System Architecture

## 1. Architectural Overview

The `credit-assessment-system` is designed as a modular credit assessment prototype that separates **deterministic assessment logic** from **LLM-based reporting**.

The system follows a layered architecture in which each component has a clearly defined responsibility.

The fundamental architectural principle is:

> **The deterministic assessment engine makes the assessment; the LLM only supports the reporting process.**

The LLM therefore has no authority to determine or modify the final credit assessment status.

The high-level processing flow is:

```text
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
      ├───────────────┐
      ▼               ▼
LLM Report      Deterministic Report
Generator          Generator
      │               │
      └───────┬───────┘
              ▼
            Report
```

---

# 2. High-Level Architecture

The system is organized into the following conceptual layers:

```text
┌──────────────────────────────────────────────────────────┐
│                    ORCHESTRATION                         │
│                                                          │
│              Orchestrator / Workflow                    │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    ASSESSMENT                            │
│                                                          │
│     Assessment Service → Rule Engine → Rules             │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                     ANALYSIS                             │
│                                                          │
│                    Analysis Agent                        │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    REPORTING                             │
│                                                          │
│ Reporting Agent → LLM Generator / Deterministic Generator│
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                         Report
```

This structure allows the individual components to be tested and evolved independently.

---

# 3. Deterministic Assessment Layer

The deterministic assessment layer is the authoritative part of the system.

It is responsible for evaluating the financial characteristics of a credit position and producing a structured assessment.

The layer consists primarily of:

* `CreditPosition`;
* assessment rules;
* `RuleEngine`;
* `AssessmentService`;
* `AssessmentStatus`.

The output of this layer is an `Assessment` object.

---

## 3.1 Credit Position

`CreditPosition` represents the structured financial information associated with a credit position.

Examples of monitored indicators include:

* revenue growth;
* EBITDA;
* profit/loss;
* EBITDA margin;
* PFN-to-EBITDA;
* interest expense.

The position is intentionally represented as structured domain data rather than natural-language input.

This provides deterministic and testable inputs to the assessment engine.

---

## 3.2 Rule Engine

The rule engine evaluates the financial indicators using explicit business rules.

Each rule encapsulates a specific assessment condition.

Examples include:

```text
Revenue Growth Rule
Negative EBITDA Rule
EBITDA Margin Rule
PFN-to-EBITDA Rule
Financial Expense-to-EBITDA Rule
EBITDA Inventory Contribution Rule
```

Rules return structured results rather than directly modifying the overall assessment.

This provides a clear separation between:

```text
Rule Evaluation
      ↓
Rule Results
      ↓
Assessment Status
```

The rule engine is therefore deterministic and independently testable.

---

## 3.3 Assessment Service

The `AssessmentService` coordinates the execution of the deterministic assessment process.

Its responsibility is to:

1. receive a `CreditPosition`;
2. execute the configured rules;
3. collect the resulting rule evaluations;
4. determine the overall assessment status;
5. produce an `Assessment`.

The service represents the main entry point into the deterministic assessment domain.

---

## 3.4 Assessment Status

The system currently supports three principal assessment states:

```text
NORMAL
ATTENTION
CRITICAL
```

The status is determined by deterministic assessment logic.

The LLM does not participate in this calculation.

This guarantees that the same structured input and rule configuration produce the same assessment result.

---

# 4. Analysis Layer

The analysis layer transforms the structured assessment into a representation suitable for reporting.

It is implemented through the `AnalysisAgent`.

The analysis layer does not independently reassess the credit position.

Instead, it interprets the deterministic assessment results and organizes them into an `AssessmentAnalysis`.

The resulting structure contains elements such as:

* assessment status;
* key findings;
* risk factors;
* limitations.

The flow is:

```text
Assessment
    │
    ▼
Analysis Agent
    │
    ▼
AssessmentAnalysis
```

The assessment status is explicitly preserved during this transformation.

---

## 4.1 Analysis Agent

The `AnalysisAgent` acts as the boundary between assessment and reporting.

Its responsibility is to transform:

```text
Assessment → AssessmentAnalysis
```

without introducing an independent decision-making mechanism.

This separation is important because reporting requirements may evolve independently from the underlying assessment rules.

---

## 4.2 Assessment Analysis

`AssessmentAnalysis` is the structured representation consumed by the reporting layer.

It separates information into distinct categories:

```text
Assessment Status
       │
       ├── Key Findings
       │
       ├── Risk Factors
       │
       └── Limitations
```

This structure provides a controlled input to the LLM.

The LLM therefore operates on already-processed and structured information rather than raw financial data.

---

# 5. Reporting Layer

The reporting layer is responsible for producing the final `Report`.

The central component is the `ReportingAgent`.

The reporting layer supports two report generation strategies:

1. deterministic reporting;
2. LLM-based reporting.

Both generators implement the same `ReportGenerator` abstraction.

This allows the reporting mechanism to be replaced without changing the rest of the workflow.

---

## 5.1 Reporting Agent

The `ReportingAgent` receives an `AssessmentAnalysis` and delegates report generation to the configured `ReportGenerator`.

Conceptually:

```text
AssessmentAnalysis
        │
        ▼
ReportingAgent
        │
        ▼
ReportGenerator
```

The reporting agent does not contain the actual reporting logic.

Instead, it delegates that responsibility to the selected generator.

This follows the principle of separation of concerns.

---

## 5.2 Deterministic Report Generator

`DeterministicReportGenerator` produces a report without using an external LLM.

Its executive summary is generated from the deterministic assessment status.

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

The structured findings and limitations are preserved from the analysis.

The deterministic generator therefore provides a predictable reporting mechanism and acts as the system's fallback reporting implementation.

---

## 5.3 LLM Report Generator

`LLMReportGenerator` uses an implementation of the `LLMClient` abstraction to generate the executive summary.

The generator constructs a controlled prompt from the `AssessmentAnalysis`.

The prompt contains:

* assessment status;
* key findings;
* risk factors;
* limitations;
* explicit reporting constraints.

The LLM is instructed to:

* use only the supplied assessment information;
* avoid inventing financial information;
* avoid changing the assessment status;
* avoid making credit decisions;
* avoid unsupported recommendations;
* distinguish findings from limitations;
* use professional credit-risk language.

The generated response is then validated before being included in the final report.

---

# 6. LLM Integration

The LLM integration is isolated behind the `LLMClient` abstraction.

This prevents the reporting layer from being directly coupled to a specific LLM provider.

The architecture is:

```text
LLMReportGenerator
        │
        ▼
    LLMClient
        │
        ├───────────────┐
        ▼               ▼
 MockLLMClient     GeminiClient
```

---

## 6.1 LLM Client Abstraction

`LLMClient` defines the interface required by the reporting layer.

The reporting system therefore depends on an abstraction rather than a specific implementation.

This provides:

* testability;
* provider independence;
* easier replacement of the underlying model;
* separation between application logic and external services.

---

## 6.2 Mock LLM Client

`MockLLMClient` is used for automated tests.

It provides deterministic responses without requiring access to an external LLM service.

This is particularly important for unit and integration testing because test results should not depend on:

* network availability;
* external API availability;
* model randomness;
* API costs.

---

## 6.3 Gemini Client

`GeminiClient` provides the real LLM integration.

It is used during scenario-based validation to evaluate the complete workflow using an actual LLM service.

The provider-specific implementation remains isolated from the rest of the architecture.

---

# 7. LLM Response Validation

The LLM response is treated as **untrusted generated content**.

Before being accepted by the reporting layer, it is validated against the structured assessment.

The validation checks include:

```text
Generated Response
        │
        ▼
Non-empty?
        │
        ▼
Correct Assessment Status?
        │
        ▼
Required Key Findings Present?
        │
        ▼
Required Risk Factors Present?
        │
        ▼
Validated Response
```

If validation fails, the generated response is rejected.

This prevents the LLM from silently producing a report that is inconsistent with the structured assessment.

---

# 8. Fallback Architecture

The reporting architecture includes a deterministic fallback mechanism.

The `ReportingAgent` accepts:

```text
primary report generator
fallback report generator
```

When the primary generator fails, the reporting agent invokes the fallback generator.

The current intended configuration is:

```text
Primary:
LLMReportGenerator

Fallback:
DeterministicReportGenerator
```

The resulting architecture is:

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
          success                   failure
             │                         │
             ▼                         ▼
        LLM Report          DeterministicReportGenerator
             │                         │
             └────────────┬────────────┘
                          ▼
                        Report
```

The fallback ensures that failure of the external LLM service does not invalidate the deterministic assessment.

---

# 9. Workflow Orchestration

The `AssessmentWorkflow` coordinates the main processing stages.

Its responsibility is orchestration rather than business-rule evaluation.

The workflow executes:

```text
1. Assessment
2. Analysis
3. Reporting
```

More precisely:

```text
CreditPosition
      │
      ▼
AssessmentService.assess()
      │
      ▼
Assessment
      │
      ▼
AnalysisAgent.run()
      │
      ▼
AssessmentAnalysis
      │
      ▼
ReportingAgent.run()
      │
      ▼
Report
```

The workflow returns an `AssessmentWorkflowResult` containing:

* assessment;
* analysis;
* report.

This provides access to the structured result of each processing stage.

---

# 10. Orchestration Layer

The system also provides an orchestration layer responsible for executing the complete workflow from the application level.

The orchestration layer hides the internal construction of the workflow from the caller.

Conceptually:

```text
Application
     │
     ▼
Orchestrator
     │
     ▼
AssessmentWorkflow
     │
     ├── Assessment Service
     ├── Analysis Agent
     └── Reporting Agent
```

This provides a single entry point for executing the credit assessment process.

---

# 11. Separation of Responsibilities

The architecture intentionally separates the system into distinct responsibilities.

| Component                      | Responsibility                                  |
| ------------------------------ | ----------------------------------------------- |
| `CreditPosition`               | Represents financial input data                 |
| Rules                          | Evaluate individual financial conditions        |
| `RuleEngine`                   | Executes and aggregates rule evaluations        |
| `AssessmentService`            | Produces the deterministic assessment           |
| `AnalysisAgent`                | Structures assessment information for reporting |
| `AssessmentAnalysis`           | Represents structured reporting information     |
| `ReportingAgent`               | Coordinates report generation                   |
| `DeterministicReportGenerator` | Generates deterministic reports                 |
| `LLMReportGenerator`           | Generates natural-language reports using an LLM |
| `LLMClient`                    | Abstracts the LLM provider                      |
| `MockLLMClient`                | Provides deterministic LLM behavior for testing |
| `GeminiClient`                 | Provides real LLM integration                   |
| `AssessmentWorkflow`           | Coordinates assessment, analysis, and reporting |
| `Orchestrator`                 | Provides application-level workflow execution   |

This separation reduces coupling between the deterministic domain and the generative component.

---

# 12. Architectural Principles

## 12.1 Deterministic Decision Logic

The assessment decision is produced exclusively by explicit and deterministic rules.

The LLM cannot determine:

* whether a position is `NORMAL`;
* whether a position requires `ATTENTION`;
* whether a position is `CRITICAL`.

This makes the assessment logic transparent and reproducible.

---

## 12.2 Separation of Decision and Reporting

Decision-making and natural-language generation are intentionally separated.

```text
Decision
   ↓
Deterministic

Reporting
   ↓
Deterministic or LLM-based
```

This allows the reporting technology to change without changing the underlying assessment logic.

---

## 12.3 Dependency Inversion

Higher-level components depend on abstractions rather than concrete implementations.

For example:

```text
ReportingAgent
      ↓
ReportGenerator
      ↓
LLMReportGenerator
DeterministicReportGenerator
```

Similarly:

```text
LLMReportGenerator
      ↓
LLMClient
      ↓
GeminiClient / MockLLMClient
```

This improves testability and extensibility.

---

## 12.4 Single Responsibility

Each major component has a focused responsibility.

For example:

* rules evaluate individual conditions;
* the rule engine executes rules;
* the assessment service coordinates assessment;
* the analysis agent structures results;
* the reporting agent coordinates reporting;
* report generators generate reports;
* the LLM client communicates with the external model.

This limits the amount of logic that must change when a specific component evolves.

---

## 12.5 Explicit Data Flow

The system uses explicit domain objects to communicate between stages.

The principal data flow is:

```text
CreditPosition
      ↓
Assessment
      ↓
AssessmentAnalysis
      ↓
Report
```

This makes intermediate results observable and testable.

---

## 12.6 Controlled Use of Generative AI

The LLM is deliberately constrained to the reporting layer.

It is not used for:

* rule evaluation;
* assessment classification;
* threshold selection;
* credit decisions;
* modification of structured assessment results.

Its role is limited to transforming structured information into a professional natural-language executive summary.

This design reduces the potential impact of hallucination or inconsistent model behavior on the deterministic assessment process.

---

# 13. Architectural Boundary

The most important boundary in the system is the separation between the deterministic domain and the generative reporting component.

```text
┌─────────────────────────────────────────────────────────┐
│                 DETERMINISTIC DOMAIN                    │
│                                                         │
│ CreditPosition                                          │
│       ↓                                                 │
│ Rules                                                   │
│       ↓                                                 │
│ RuleEngine                                               │
│       ↓                                                 │
│ AssessmentService                                       │
│       ↓                                                 │
│ Assessment                                               │
│       ↓                                                 │
│ AssessmentAnalysis                                      │
│                                                         │
│             AUTHORITATIVE ASSESSMENT                    │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  GENERATIVE LAYER                       │
│                                                         │
│ LLMReportGenerator                                      │
│       ↓                                                 │
│ LLMClient                                               │
│       ↓                                                 │
│ External LLM                                            │
│                                                         │
│             REPORTING ONLY                               │
└─────────────────────────────────────────────────────────┘
```

This boundary is a core design decision of the system.

The deterministic domain remains authoritative even when the generative component is unavailable.

---

# 14. Architectural Rationale

The architecture intentionally avoids placing the LLM at the center of the credit assessment process.

A fully LLM-driven assessment could introduce unnecessary uncertainty into a process that benefits from:

* reproducibility;
* traceability;
* explicit rules;
* deterministic outcomes;
* testability.

Instead, the system uses a hybrid architecture:

```text
Deterministic Logic
        +
Generative Reporting
```

This provides a practical balance between transparency and natural-language generation.

The deterministic layer provides control and explainability, while the LLM provides flexibility in communicating the results.

---

# 15. Current Scope

The current architecture is intentionally designed as a prototype.

It provides the core infrastructure required to demonstrate:

* rule-based credit assessment;
* structured analysis;
* modular reporting;
* LLM integration;
* LLM response validation;
* deterministic fallback;
* end-to-end orchestration.

The architecture does not currently introduce additional infrastructure such as:

* databases;
* REST APIs;
* web applications;
* message queues;
* distributed services;
* container orchestration;
* vector databases;
* retrieval-augmented generation.

These technologies are not required for the current assessment prototype and can be introduced only if future requirements justify their use.
