# System Architecture

## 1. Architectural Overview

The `credit-assessment-system` is a modular prototype for credit assessment designed around a **hybrid deterministic–generative architecture**.

The system deliberately separates two fundamentally different responsibilities:

1. **Credit assessment**, which is performed exclusively through deterministic and explicitly configured business rules.
2. **Report generation**, where an LLM may be used to transform structured assessment results into a concise natural-language executive summary.

The core architectural principle is:

> **The deterministic assessment engine is the source of truth; the LLM is a reporting component with no decision-making authority.**

Consequently, the LLM cannot:

* determine the overall assessment status;
* modify rule results;
* modify rule thresholds;
* modify rule severity;
* introduce new findings into the structured assessment;
* remove deterministic findings;
* change limitations;
* make an independent credit decision.

The system therefore combines the reproducibility and traceability of deterministic logic with the flexibility of generative natural-language reporting.

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
      ├──────────────────────┐
      ▼                      ▼
LLM Report Generator   Deterministic Report Generator
      │                      │
      └───────────┬──────────┘
                  ▼
                Report
```

This architecture establishes a strict boundary between **assessment authority** and **natural-language generation**.

---

# 2. Architectural Goals

The architecture has been designed around the following objectives:

* **Determinism** — identical inputs and rule configurations should produce identical assessment results.
* **Traceability** — each assessment result should be attributable to explicit rules and structured findings.
* **Explainability** — the system should expose the reasoning chain from financial indicators to assessment findings.
* **Modularity** — individual components should be replaceable without redesigning the entire system.
* **Testability** — deterministic components should be testable without external dependencies.
* **LLM isolation** — external generative services should not directly influence the assessment domain.
* **Fault tolerance** — failure of the LLM service should not invalidate the deterministic assessment.
* **Provider independence** — the reporting layer should not depend directly on a specific LLM provider.

These goals lead to a layered architecture in which responsibilities are explicitly separated.

---

# 3. High-Level Architecture

The system can be conceptually divided into five layers:

```text
┌──────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                     │
│                                                          │
│                  Orchestrator                            │
│                       │                                  │
│                  AssessmentWorkflow                      │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  ASSESSMENT LAYER                        │
│                                                          │
│ CreditPosition → AssessmentService → RuleEngine → Rules │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                        │
│                                                          │
│                    AnalysisAgent                        │
│                           │                              │
│                           ▼                              │
│                  AssessmentAnalysis                      │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                   REPORTING LAYER                        │
│                                                          │
│                  ReportingAgent                         │
│                       │                                  │
│              ┌────────┴─────────┐                        │
│              ▼                  ▼                        │
│      LLMReportGenerator   DeterministicReportGenerator │
└──────────────┬──────────────────┬────────────────────────┘
               │                  │
               ▼                  │
          LLMClient               │
               │                  │
        ┌──────┴──────┐           │
        ▼             ▼           │
   GeminiClient  MockLLMClient     │
               │                  │
               └────────┬─────────┘
                        ▼
                      Report
```

The architecture deliberately keeps the LLM below the reporting boundary.

The deterministic assessment path does not depend on the availability of the LLM.

---

# 4. Domain and Assessment Layer

The assessment layer represents the core business logic of the system.

It is responsible for evaluating the financial characteristics of a credit position using explicitly defined rules.

The main components are:

* `CreditPosition`;
* individual assessment rules;
* `RuleEngine`;
* `AssessmentService`;
* `Assessment`;
* `AssessmentStatus`.

The output of this layer is an `Assessment` object containing the structured results of the deterministic assessment process.

---

## 4.1 Credit Position

`CreditPosition` represents the structured financial information associated with a credit position.

Current indicators include:

* revenue growth;
* EBITDA;
* profit/loss;
* EBITDA margin;
* PFN-to-EBITDA;
* interest expense.

The position is represented as structured domain data rather than natural-language input.

For example:

```text
CreditPosition
├── position_id
├── revenue_growth
├── ebitda
├── profit_loss
├── ebitda_margin
├── pfn_to_ebitda
└── interest_expense
```

This design ensures that rule evaluation operates on explicit and typed inputs.

It also makes the assessment process easier to reproduce and test.

---

# 5. Rule Architecture

The rule architecture encapsulates individual credit-risk conditions.

Each rule evaluates a specific financial indicator or relationship and returns a structured `RuleResult`.

Examples of currently implemented rules include:

```text
Revenue Growth Rule
Negative EBITDA Rule
EBITDA Margin Rule
PFN-to-EBITDA Rule
Financial Expenses-to-EBITDA Rule
EBITDA Inventory Contribution Rule
Interest Coverage Ratio Rule
```

The conceptual processing chain is:

```text
Financial Indicator
        │
        ▼
Business Rule
        │
        ▼
RuleResult
        │
        ├── rule_id
        ├── category
        ├── value
        ├── threshold
        ├── status
        └── severity
```

Rules do not directly determine the overall credit assessment.

Instead, they provide structured evidence that is subsequently aggregated by the assessment layer.

This separation is important because it prevents individual rules from becoming coupled to the overall assessment workflow.

---

## 5.1 Rule Configuration

Rule behavior is separated from the rule implementation through `RuleConfig`.

A configuration can define:

* rule identifier;
* rule name;
* category;
* primary threshold;
* default severity;
* severity direction;
* severity thresholds.

For example:

```text
Rule
 │
 ├── RuleConfig
 │     ├── threshold
 │     ├── severity
 │     ├── severity_direction
 │     └── severity_thresholds
 │
 └── evaluate()
```

`SeverityThreshold` represents a threshold associated with a specific severity level.

This allows the severity policy to be configured independently from the rule implementation.

The rule therefore contains the **calculation logic**, while the configuration contains the **business parameters**.

---

# 6. Rule Engine

The `RuleEngine` is responsible for executing the configured rules against a `CreditPosition`.

Its responsibilities include:

1. receiving the credit position;
2. executing the applicable rules;
3. collecting their `RuleResult` objects;
4. returning the structured rule evaluation results.

The rule engine does not generate natural-language explanations and does not invoke the LLM.

Its role is strictly deterministic.

The resulting architecture is:

```text
CreditPosition
      │
      ▼
   RuleEngine
      │
      ├── Rule 1 → RuleResult
      ├── Rule 2 → RuleResult
      ├── Rule 3 → RuleResult
      └── Rule N → RuleResult
```

This makes rule evaluation independently testable.

---

# 7. Assessment Service

The `AssessmentService` coordinates the deterministic assessment process.

Its responsibilities are to:

1. receive a `CreditPosition`;
2. invoke the configured rule engine;
3. collect the resulting rule evaluations;
4. generate structured findings;
5. determine the overall assessment status;
6. return an `Assessment`.

Conceptually:

```text
CreditPosition
      │
      ▼
AssessmentService
      │
      ├── RuleEngine
      │      │
      │      └── RuleResults
      │
      ├── Findings
      │
      └── AssessmentStatus
             │
             ▼
         Assessment
```

The assessment service therefore acts as the main application-level entry point into the deterministic assessment domain.

---

# 8. Assessment Status

The system currently supports three principal assessment states:

```text
NORMAL
ATTENTION
CRITICAL
```

The overall status is calculated exclusively from deterministic assessment results.

The LLM has no role in this calculation.

Therefore:

```text
CreditPosition
      │
      ▼
Deterministic Rules
      │
      ▼
Assessment Status
```

and never:

```text
CreditPosition
      │
      ▼
LLM
      │
      ▼
Assessment Status
```

This distinction is one of the most important architectural guarantees of the system.

For a fixed position and fixed rule configuration:

```text
Same Input + Same Configuration
                │
                ▼
       Same Assessment Result
```

---

# 9. Finding Generation

The assessment layer produces structured findings from triggered rule evaluations.

A finding preserves the relationship between the underlying rule result and its human-readable explanation.

Conceptually:

```text
RuleResult
    │
    ▼
Finding
├── Rule Result
└── Comment
```

This provides traceability from the final report back to the deterministic rule that generated the finding.

The reporting layer therefore does not need to rediscover why a finding exists.

---

# 10. Analysis Layer

The analysis layer transforms the deterministic `Assessment` into an `AssessmentAnalysis`.

It is implemented through the `AnalysisAgent`.

The analysis agent does **not** perform a second credit assessment.

Instead, it organizes the information already produced by the deterministic assessment layer into a representation suitable for reporting.

The transformation is:

```text
Assessment
    │
    ▼
AnalysisAgent
    │
    ▼
AssessmentAnalysis
```

The resulting structure contains:

* assessment status;
* key findings;
* risk factors;
* limitations.

The assessment status is propagated directly from the deterministic assessment.

---

## 10.1 AssessmentAnalysis

`AssessmentAnalysis` acts as a controlled boundary between assessment and reporting.

Its structure can be represented as:

```text
AssessmentAnalysis
│
├── Assessment Status
├── Key Findings
├── Risk Factors
└── Limitations
```

This intermediate representation has two important purposes:

1. it separates assessment logic from report generation;
2. it provides the LLM with structured and controlled information.

The LLM therefore does not need to reason over the raw assessment pipeline.

It receives an already structured representation of the assessment.

---

# 11. Reporting Layer

The reporting layer transforms `AssessmentAnalysis` into a final `Report`.

The central coordinator is the `ReportingAgent`.

The architecture supports two report-generation strategies:

1. `DeterministicReportGenerator`;
2. `LLMReportGenerator`.

Both implement the `ReportGenerator` abstraction.

This allows the reporting strategy to be changed without modifying the assessment or analysis layers.

```text
AssessmentAnalysis
        │
        ▼
ReportingAgent
        │
        ▼
ReportGenerator
        │
        ├── LLMReportGenerator
        │
        └── DeterministicReportGenerator
```

---

# 12. Reporting Agent

The `ReportingAgent` is responsible for coordinating report generation.

It receives:

```text
AssessmentAnalysis
```

and delegates generation to the configured `ReportGenerator`.

The reporting agent also implements the fallback mechanism.

Its conceptual behavior is:

```text
ReportingAgent
      │
      ▼
Primary Report Generator
      │
      ├── Success ──────────► Report
      │
      └── Failure
             │
             ▼
      Fallback Generator
             │
             ▼
           Report
```

The reporting agent therefore separates:

* **report orchestration** from
* **report generation**.

It also maintains runtime diagnostics such as:

* `last_generator_used`;
* `last_error`.

These values provide basic observability of the reporting path.

---

# 13. Deterministic Report Generator

`DeterministicReportGenerator` produces a report without requiring an external LLM.

Its primary purpose is to provide:

* predictable reporting;
* offline execution;
* testability;
* a reliable fallback mechanism.

The deterministic generator receives the same `AssessmentAnalysis` used by the LLM generator.

Structured findings and limitations are therefore preserved regardless of the selected reporting strategy.

Conceptually:

```text
AssessmentAnalysis
        │
        ▼
DeterministicReportGenerator
        │
        ▼
      Report
```

This generator is particularly important from a resilience perspective because it guarantees that failure of an external generative service does not prevent report production.

---

# 14. LLM Report Generator

`LLMReportGenerator` provides the generative reporting implementation.

Its responsibility is intentionally narrow:

> Generate a natural-language executive summary from the structured `AssessmentAnalysis`.

The generator:

1. builds a controlled prompt;
2. sends the prompt to an `LLMClient`;
3. receives the generated response;
4. validates the response;
5. constructs the final `Report`.

The structured findings and limitations are not generated by the LLM.

They are propagated directly from the deterministic analysis.

Therefore:

```text
AssessmentAnalysis
       │
       ├───────────────► Findings
       │
       ├───────────────► Limitations
       │
       ▼
LLMReportGenerator
       │
       ▼
Executive Summary
       │
       └───────────────┐
                       ▼
                     Report
```

This is a critical architectural property: **the LLM generates only the narrative component of the report.**

---

# 15. Controlled LLM Prompt

The prompt constructed by `LLMReportGenerator` explicitly constrains the model.

The current prompt instructs the model to:

* use exclusively the supplied assessment information;
* avoid introducing unsupported facts;
* avoid inventing financial data;
* avoid inventing causes or trends;
* preserve the assessment status;
* avoid making credit decisions;
* avoid unsupported recommendations;
* distinguish findings from limitations;
* avoid inferring missing information;
* use professional credit-risk terminology;
* avoid disclosing internal rule thresholds;
* avoid reproducing threshold values.

This establishes a **prompt-level safety boundary**.

However, prompt instructions are not treated as a sufficient technical guarantee.

The generated response is also validated before acceptance.

---

# 16. LLM Response Validation

The LLM response is treated as **untrusted generated content**.

The current validation layer performs two fundamental checks:

```text
LLM Response
      │
      ▼
Is the response non-empty?
      │
      ▼
Does it contain the deterministic assessment status?
      │
      ▼
Validated Response
```

If the response is empty or does not contain the expected assessment status, validation fails.

The reporting agent then activates the deterministic fallback.

This creates the following control mechanism:

```text
LLM Output
    │
    ▼
Validation
    │
    ├── Valid ──────► Report
    │
    └── Invalid
           │
           ▼
      Fallback Report
```

### Future validation extensions

The architecture can be extended with stronger semantic validation, for example:

* checking that required findings are reflected in the summary;
* checking consistency of reported metrics;
* detecting unsupported claims;
* detecting contradictions with deterministic findings;
* validating structured LLM output against a schema.

These extensions are not currently required for the core prototype but fit naturally within the existing architecture.

---

# 17. LLM Integration

The LLM integration is isolated behind the `LLMClient` abstraction.

The reporting layer therefore does not depend directly on Gemini or another specific provider.

```text
LLMReportGenerator
        │
        ▼
     LLMClient
        │
        ├───────────────┐
        ▼               ▼
 GeminiClient      MockLLMClient
```

This follows the Dependency Inversion Principle and provides provider independence.

---

# 18. LLM Client Abstraction

`LLMClient` defines the interface required by the reporting layer.

The application therefore depends on:

```text
LLMClient
```

rather than:

```text
GeminiClient
```

This allows the underlying provider to be replaced without modifying `LLMReportGenerator`.

Potential future implementations could include:

```text
GeminiClient
OpenAIClient
LocalLLMClient
MockLLMClient
```

without changing the reporting architecture.

---

# 19. Mock LLM Client

`MockLLMClient` provides deterministic LLM behavior for automated testing.

It avoids dependencies on:

* network connectivity;
* external API availability;
* API quotas;
* model stochasticity;
* API costs.

The mock also stores the last generated prompt, allowing tests to verify prompt construction when required.

This makes the LLM-dependent reporting layer fully testable without invoking an external model.

---

# 20. Gemini Client

`GeminiClient` provides the concrete integration with the Gemini API.

Provider-specific concerns remain isolated within this component.

The rest of the application interacts only with the `LLMClient` abstraction.

This separation limits the impact of provider-specific changes on the application architecture.

---

# 21. Fallback Architecture

The reporting architecture implements graceful degradation.

The `ReportingAgent` can be configured with:

```text
Primary Generator
+
Fallback Generator
```

The intended production-like configuration is:

```text
Primary:
LLMReportGenerator

Fallback:
DeterministicReportGenerator
```

The complete execution path is:

```text
                    ReportingAgent
                          │
                          ▼
                 LLMReportGenerator
                          │
                    generate()
                          │
             ┌────────────┴────────────┐
             │                         │
          success                   exception
             │                         │
             ▼                         ▼
       Validate response       Record failure
             │                         │
             │                         ▼
             │              DeterministicReportGenerator
             │                         │
             └────────────┬────────────┘
                          ▼
                        Report
```

The fallback mechanism is important because the external LLM is not part of the deterministic assessment domain.

An unavailable or malfunctioning LLM therefore affects **report generation**, but not **credit assessment**.

---

# 22. Error Handling and Observability

The `ReportingAgent` records basic runtime diagnostics.

Two diagnostic attributes are maintained:

```text
last_generator_used
last_error
```

`last_generator_used` identifies whether the report was generated by:

```text
PRIMARY
```

or:

```text
FALLBACK
```

`last_error` stores a concise human-readable description of the failure encountered by the primary generator.

Provider-specific failures are normalized into application-level messages.

Examples include:

```text
Gemini API quota exceeded.
Gemini service is temporarily unavailable.
Gemini API authentication failed.
Gemini API access was denied.
Gemini request timed out.
LLM report generation failed.
```

This prevents low-level provider errors from unnecessarily leaking into the application-facing reporting layer.

---

# 23. Workflow Orchestration

`AssessmentWorkflow` coordinates the three main processing stages:

```text
1. Assessment
2. Analysis
3. Reporting
```

The complete workflow is:

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

* `assessment`;
* `analysis`;
* `report`.

This intermediate representation is useful for both application logic and testing because each stage remains observable.

---

# 24. Application-Level Orchestration

The `Orchestrator` provides a higher-level entry point for executing the complete assessment workflow.

Its purpose is to hide the internal construction and coordination of the workflow components.

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
     ├── AssessmentService
     ├── AnalysisAgent
     └── ReportingAgent
```

This allows the caller to execute the complete process without needing to manually construct the individual components.

---

# 25. Factory Pattern

The project uses factory functions to centralize component construction.

Examples include:

```text
create_default_assessment_workflow()
create_default_orchestrator()
```

Factories encapsulate configuration and dependency wiring.

For example:

```text
create_default_assessment_workflow()
            │
            ├── AssessmentService
            ├── AnalysisAgent
            ├── ReportingAgent
            ├── LLMReportGenerator
            └── DeterministicReportGenerator
```

This prevents application code from becoming tightly coupled to concrete implementation details.

It also provides a single location where the default architecture can be configured.

---

# 26. Separation of Responsibilities

The main architectural responsibilities can be summarized as follows:

| Component                      | Responsibility                                                 |
| ------------------------------ | -------------------------------------------------------------- |
| `CreditPosition`               | Represents structured financial input data                     |
| Rules                          | Evaluate individual financial conditions                       |
| `RuleConfig`                   | Defines configurable rule parameters                           |
| `SeverityThreshold`            | Maps configured thresholds to severity levels                  |
| `RuleEngine`                   | Executes deterministic rules                                   |
| `AssessmentService`            | Coordinates deterministic assessment                           |
| `Assessment`                   | Represents the structured assessment result                    |
| `AnalysisAgent`                | Transforms assessment results into reporting-oriented analysis |
| `AssessmentAnalysis`           | Represents structured analysis information                     |
| `ReportingAgent`               | Coordinates report generation and fallback                     |
| `ReportGenerator`              | Defines the report-generation abstraction                      |
| `DeterministicReportGenerator` | Generates deterministic reports                                |
| `LLMReportGenerator`           | Generates natural-language executive summaries                 |
| `LLMClient`                    | Abstracts communication with an LLM provider                   |
| `MockLLMClient`                | Provides deterministic LLM behavior for testing                |
| `GeminiClient`                 | Provides the concrete Gemini integration                       |
| `Report`                       | Represents the final report                                    |
| `AssessmentWorkflow`           | Coordinates assessment, analysis, and reporting                |
| `Orchestrator`                 | Provides application-level workflow execution                  |
| Factory functions              | Centralize dependency construction and configuration           |

---

# 27. Data Flow and Information Ownership

An important architectural property is that each processing stage owns a specific type of information.

```text
CreditPosition
      │
      │  Structured financial inputs
      ▼
Assessment
      │
      │  Rule results + deterministic status
      ▼
AssessmentAnalysis
      │
      │  Structured findings, risk factors,
      │  limitations and preserved status
      ▼
Report
      │
      │  Executive summary + structured findings
      ▼
Application / User
```

Information is progressively transformed, but deterministic information is not delegated to the LLM.

In particular:

```text
Assessment Status
       │
       ├── Assessment
       ├── AssessmentAnalysis
       └── Report
```

must remain consistent across all layers.

Similarly:

```text
Deterministic Findings
       │
       ├── Assessment
       ├── AssessmentAnalysis
       └── Report
```

must be preserved throughout the workflow.

---

# 28. Deterministic–Generative Boundary

The most important architectural boundary is between the deterministic assessment domain and the generative reporting layer.

```text
┌─────────────────────────────────────────────────────────┐
│                  DETERMINISTIC DOMAIN                   │
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
│ AnalysisAgent                                           │
│       ↓                                                 │
│ AssessmentAnalysis                                      │
│                                                         │
│              AUTHORITATIVE INFORMATION                  │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ Controlled structured input
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    GENERATIVE LAYER                     │
│                                                         │
│ ReportingAgent                                          │
│       ↓                                                 │
│ LLMReportGenerator                                      │
│       ↓                                                 │
│ LLMClient                                               │
│       ↓                                                 │
│ External LLM                                            │
│                                                         │
│              NARRATIVE GENERATION ONLY                  │
└─────────────────────────────────────────────────────────┘
```

This boundary is intentionally asymmetric.

The deterministic layer supplies authoritative information to the generative layer, but the generative layer does not feed decisions back into the deterministic domain.

Therefore, the information flow is effectively:

```text
Deterministic Domain
        │
        ▼
Generative Layer
```

and not:

```text
Deterministic Domain
        ↕
Generative Layer
```

This unidirectional dependency is a key safety and architectural property.

---

# 29. Architectural Principles

## 29.1 Deterministic Decision Logic

Credit assessment decisions are produced exclusively through explicit rules and deterministic status-calculation logic.

The LLM cannot determine whether a position is:

```text
NORMAL
ATTENTION
CRITICAL
```

This guarantees reproducibility and makes the decision process auditable.

---

## 29.2 Separation of Decision and Reporting

Decision-making and natural-language generation are treated as separate concerns.

```text
Assessment
    ↓
Deterministic

Reporting
    ↓
Deterministic OR Generative
```

Consequently, the reporting technology can evolve without changing the underlying assessment logic.

---

## 29.3 Dependency Inversion

Higher-level components depend on abstractions rather than concrete implementations.

For example:

```text
ReportingAgent
      ↓
ReportGenerator
      ↓
├── LLMReportGenerator
└── DeterministicReportGenerator
```

and:

```text
LLMReportGenerator
      ↓
LLMClient
      ↓
├── GeminiClient
└── MockLLMClient
```

This improves testability, maintainability and extensibility.

---

## 29.4 Single Responsibility

Each major component has a focused responsibility.

For example:

* rules evaluate individual financial conditions;
* the rule engine executes rules;
* the assessment service coordinates assessment;
* the analysis agent structures assessment results;
* the reporting agent coordinates report generation;
* report generators generate reports;
* the LLM client communicates with the external model;
* the orchestrator coordinates application-level execution.

This limits coupling and reduces the potential impact of future changes.

---

## 29.5 Explicit Data Contracts

The system communicates between layers through explicit domain objects:

```text
CreditPosition
Assessment
AssessmentAnalysis
Report
```

These objects act as data contracts between architectural stages.

This improves:

* readability;
* testability;
* traceability;
* interface stability.

---

## 29.6 Controlled Use of Generative AI

The LLM is deliberately restricted to the reporting layer.

It is not used for:

* rule evaluation;
* threshold selection;
* severity determination;
* assessment classification;
* credit decisions;
* modification of deterministic findings;
* modification of assessment limitations.

Its role is limited to transforming structured assessment information into professional natural-language reporting.

---

## 29.7 Graceful Degradation

The system is designed so that an external LLM failure does not cause failure of the core assessment process.

The architecture therefore distinguishes:

```text
Assessment Availability
        ≠
LLM Availability
```

The deterministic assessment remains operational even if:

* the API is unavailable;
* the API quota is exceeded;
* authentication fails;
* the request times out;
* the model produces an invalid response.

The reporting layer falls back to deterministic report generation.

---

# 30. Testing Strategy and Architectural Verification

The architecture is designed to support verification of the deterministic–generative boundary.

The test suite verifies, among other properties, that:

### Deterministic assessment remains authoritative

```text
Assessment.status
        ==
Analysis.assessment_status
        ==
Report.assessment_status
```

### Deterministic findings are preserved

```text
Assessment findings
        ↓
Analysis findings
        ↓
Report findings
```

### LLM output is limited to the executive summary

The LLM does not replace the structured findings or limitations contained in the deterministic pipeline.

### Invalid LLM responses trigger fallback

For example:

```text
Empty response
      ↓
Validation failure
      ↓
Deterministic fallback
```

or:

```text
Missing assessment status
      ↓
Validation failure
      ↓
Deterministic fallback
```

### External service failures trigger fallback

```text
LLM exception
      ↓
ReportingAgent
      ↓
DeterministicReportGenerator
```

This testing strategy directly verifies the architectural guarantees rather than testing only individual implementation details.

---

# 31. Architectural Rationale

A fully LLM-driven credit assessment could introduce uncertainty into a process that benefits from:

* reproducibility;
* explicit business rules;
* deterministic outcomes;
* traceability;
* auditability;
* controlled testing.

The system therefore adopts a hybrid architecture:

```text
Deterministic Assessment
          +
Generative Reporting
```

The deterministic layer provides:

* decision consistency;
* traceability;
* explicit business logic;
* controlled severity and threshold configuration.

The generative layer provides:

* natural-language generation;
* flexible executive summaries;
* improved communication of structured results.

The two capabilities are therefore complementary rather than interchangeable.

---

# 32. Current Scope

The current architecture is intentionally designed as a prototype focused on demonstrating the core assessment and reporting concepts.

It currently provides:

* deterministic rule-based credit assessment;
* configurable rules and severity policies;
* structured findings;
* analysis transformation;
* modular deterministic reporting;
* LLM-based reporting;
* LLM client abstraction;
* mock LLM support;
* Gemini integration;
* LLM response validation;
* deterministic fallback;
* workflow orchestration;
* application-level orchestration;
* automated unit and integration testing.

The architecture does not currently require additional infrastructure such as:

* relational or NoSQL databases;
* REST APIs;
* web frontends;
* message queues;
* distributed services;
* container orchestration;
* vector databases;
* retrieval-augmented generation;
* persistent model memory.

These components can be introduced in future iterations if justified by concrete requirements.

---

# 33. Future Extension Points

The current architecture provides several natural extension points.

## 33.1 Additional Rules

New financial indicators can be introduced as additional rule implementations without changing the overall workflow.

```text
New Rule
   ↓
RuleEngine
   ↓
AssessmentService
```

The remaining layers can continue to operate unchanged.

---

## 33.2 Additional LLM Providers

A new provider can be introduced by implementing `LLMClient`.

```text
LLMClient
   ├── GeminiClient
   ├── MockLLMClient
   └── FutureProviderClient
```

The reporting architecture remains unchanged.

---

## 33.3 Local LLM

A local model can be introduced through another `LLMClient` implementation.

For example:

```text
LLMReportGenerator
        │
        ▼
    LLMClient
        │
        ├── GeminiClient
        └── LocalLLMClient
```

This would allow experimentation with locally hosted models while preserving the existing application architecture.

---

## 33.4 Structured LLM Output

The reporting layer could be extended to require schema-constrained LLM output rather than free-form text.

For example:

```text
LLM
 │
 ▼
Structured Response
 │
 ├── Executive Summary
 ├── Mentioned Findings
 └── Risk Statements
```

The response could then be validated against the deterministic `AssessmentAnalysis` before being rendered into the final report.

---

## 33.5 Stronger Semantic Validation

The current validation layer can be extended to detect:

* unsupported claims;
* contradictions;
* missing findings;
* inconsistent financial values;
* unsupported causal explanations;
* unsupported recommendations.

This would strengthen the boundary between deterministic assessment and generated narrative.

---

# 34. Summary

The architecture implements a controlled hybrid approach to credit assessment.

The complete processing chain is:

```text
CreditPosition
      │
      ▼
Deterministic Rules
      │
      ▼
Rule Results
      │
      ▼
Assessment
      │
      ▼
AnalysisAgent
      │
      ▼
AssessmentAnalysis
      │
      ▼
ReportingAgent
      │
      ├───────────────┐
      ▼               ▼
LLM Generator   Deterministic Generator
      │               │
      └───────┬───────┘
              ▼
            Report
```

The central architectural guarantee is:

> **The deterministic assessment engine remains the authoritative source of truth, while the LLM is restricted to controlled natural-language reporting.**

This separation provides a practical combination of deterministic decision logic, traceability and explainability with the flexibility of generative AI.

Most importantly, the architecture ensures that the failure, inconsistency or unavailability of the generative component cannot alter the underlying credit assessment.
