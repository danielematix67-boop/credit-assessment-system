# System Architecture

## 1. Architectural Overview

The `credit-assessment-system` is a modular prototype for credit assessment based on a **deterministic rule engine**, a structured analysis layer, and an optional **LLM-assisted reporting layer**.

The architecture deliberately separates two fundamentally different responsibilities:

1. **Credit assessment**, which is performed exclusively through deterministic business rules and explicit configuration.
2. **Natural-language reporting**, where an LLM may be used to transform already-validated assessment information into an executive summary.

The central architectural principle is:

> **The deterministic assessment engine is the source of truth; the LLM is a reporting component with no decision-making authority.**

The LLM therefore cannot:

* determine the overall assessment status;
* evaluate credit rules;
* modify rule thresholds;
* modify rule severity;
* create new deterministic findings;
* remove deterministic findings;
* modify assessment limitations;
* make an independent credit decision.

The resulting architecture combines:

* deterministic and reproducible business logic;
* explicit rule configuration;
* structured findings;
* modular analysis;
* replaceable reporting strategies;
* controlled generative AI;
* deterministic fallback mechanisms;
* automated testing;
* provider-independent LLM integration.

The high-level processing flow is:

```text
CreditPosition
      │
      ▼
AssessmentService
      │
      ▼
RuleEngine
      │
      ├── Rule 1
      ├── Rule 2
      ├── Rule 3
      └── Rule N
      │
      ▼
RuleResult[]
      │
      ├── AssessmentStatusCalculator
      │
      └── CommentEngine
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
      ├──────────────────────────┐
      ▼                          ▼
LLMReportGenerator       DeterministicReportGenerator
      │                          │
      ▼                          │
   LLMClient                     │
      │                          │
 ┌────┴─────┐                    │
 ▼          ▼                    │
Gemini    Mock                    │
      │                          │
      └────────────┬─────────────┘
                   ▼
                 Report
```

The deterministic assessment is fully completed before the LLM reporting stage is invoked.

---

# 2. Architectural Goals

The architecture is designed around the following objectives.

## 2.1 Determinism

For a fixed `CreditPosition` and fixed rule configuration:

```text
Same Input
    +
Same Configuration
    ↓
Same Rule Results
    ↓
Same Assessment Status
```

The deterministic layer does not depend on external model behavior.

---

## 2.2 Traceability

Every assessment outcome must be traceable to structured rule evaluations.

The system preserves the relationship:

```text
CreditPosition
      ↓
Rule
      ↓
RuleResult
      ↓
RuleFinding
      ↓
Assessment
```

This makes the reasoning path inspectable and testable.

---

## 2.3 Separation of Decision and Reporting

The system explicitly separates:

```text
Decision Logic
      ↓
Assessment
      ↓
Analysis
      ↓
Reporting
```

The reporting technology can therefore change without modifying the underlying credit decision logic.

---

## 2.4 Testability

The architecture is designed so that every major component can be tested independently.

External dependencies such as an LLM API are isolated behind interfaces and can be replaced with mocks during automated testing.

---

## 2.5 Fault Isolation

Failure of an external LLM service must not invalidate the deterministic credit assessment.

The architecture therefore treats:

```text
Assessment Availability
```

and:

```text
LLM Availability
```

as independent concerns.

---

## 2.6 Provider Independence

The reporting layer depends on the `LLMClient` abstraction rather than directly on a specific provider.

The current implementation provides:

```text
LLMClient
    ├── MockLLMClient
    └── GeminiClient
```

Additional providers can be introduced without changing the reporting architecture.

---

# 3. Architectural Layers

The application can be represented through five logical layers:

```text
┌─────────────────────────────────────────────────────────┐
│                 ORCHESTRATION LAYER                     │
│                                                         │
│ Orchestrator → AssessmentWorkflow                       │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  ASSESSMENT LAYER                       │
│                                                         │
│ CreditPosition                                          │
│       ↓                                                 │
│ AssessmentService                                       │
│       ↓                                                 │
│ RuleEngine                                              │
│       ↓                                                 │
│ Rules → RuleResult[]                                    │
│       ↓                                                 │
│ Status Calculator + Comment Engine                      │
│       ↓                                                 │
│ Assessment                                              │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                       │
│                                                         │
│ AnalysisAgent                                           │
│       ↓                                                 │
│ AssessmentAnalysis                                      │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   REPORTING LAYER                       │
│                                                         │
│ ReportingAgent                                          │
│       │                                                 │
│       ├── DeterministicReportGenerator                  │
│       │                                                 │
│       └── LLMReportGenerator                            │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     LLM LAYER                           │
│                                                         │
│ LLMClient                                               │
│       ├── MockLLMClient                                 │
│       └── GeminiClient                                  │
└─────────────────────────────────────────────────────────┘
```

The most important dependency direction is:

```text
Deterministic Assessment
          │
          ▼
       Analysis
          │
          ▼
      Reporting
          │
          ▼
         LLM
```

The generative layer does not feed information back into the deterministic assessment layer.

---

# 4. Domain Model

The core domain model represents the input position and the resulting assessment.

The main objects include:

```text
CreditPosition
Assessment
AssessmentStatus
RuleResult
RuleFinding
AssessmentAnalysis
Report
```

These objects provide explicit data contracts between the architectural layers.

---

# 5. Credit Position

`CreditPosition` represents the structured financial information associated with a credit position.

The current model includes indicators such as:

```text
CreditPosition
├── position_id
├── revenue_growth
├── ebitda
├── profit_loss
├── ebitda_margin
├── nfp_to_ebitda
└── interest_expense
```

The system intentionally operates on structured domain data rather than natural-language input.

This allows rules to evaluate explicit values and makes the assessment reproducible.

Some indicators may be unavailable:

```text
revenue_growth = None
```

The rule layer explicitly represents such situations through:

```text
RuleStatus.NOT_EVALUABLE
```

rather than treating missing data as either a positive or negative result.

---

# 6. Rule Architecture

Rules represent individual deterministic credit-risk conditions.

Each rule evaluates a specific financial indicator or relationship and produces a `RuleResult`.

The conceptual flow is:

```text
Financial Data
      │
      ▼
Business Rule
      │
      ▼
RuleResult
```

A `RuleResult` contains structured information such as:

```text
rule_id
rule_name
category
status
value
threshold
severity
```

This makes every rule evaluation explicit.

---

## 6.1 Rule Status

The rule engine distinguishes between three fundamental outcomes:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

### `TRIGGERED`

The rule condition is satisfied and represents a detected risk signal.

### `NOT_TRIGGERED`

The rule was evaluated successfully and the configured risk condition was not satisfied.

### `NOT_EVALUABLE`

The rule cannot be evaluated because the required input is unavailable or insufficient.

This distinction is particularly important because:

```text
NOT_EVALUABLE ≠ TRIGGERED
```

A missing financial indicator must not automatically increase the assessment severity.

---

## 6.2 Rule Severity

Rules may associate a triggered condition with a configured severity.

The severity is determined by deterministic rule logic and configuration.

The LLM does not assign or modify severity.

Typical severity levels include:

```text
LOW
MEDIUM
HIGH
```

The exact configured levels depend on the rule implementation and configuration.

---

# 7. Rule Configuration

Rule behavior is separated from rule implementation through configuration objects.

Configuration can define:

* rule identifier;
* rule name;
* category;
* threshold;
* severity;
* severity direction;
* severity thresholds.

Conceptually:

```text
Rule
 │
 ├── RuleConfig
 │     ├── rule_id
 │     ├── threshold
 │     ├── severity
 │     ├── severity_direction
 │     └── severity_thresholds
 │
 └── evaluate()
```

This separation allows business parameters to evolve without embedding every parameter directly inside the rule implementation.

The architectural distinction is therefore:

```text
Rule Implementation
    =
How the condition is evaluated

Rule Configuration
    =
Which business parameters are applied
```

---

# 8. Rule Discovery and Registry

The project separates rule discovery and rule registration from rule execution.

The rule registry provides the configured set of rules used by the default application.

Conceptually:

```text
Rule Implementations
        │
        ▼
Rule Discovery
        │
        ▼
Rule Registry
        │
        ▼
get_default_rules()
        │
        ▼
RuleEngine
```

This allows the application to assemble the active rule set without hard-coding every rule directly inside the assessment service.

The resulting rule set is also explicitly testable.

---

# 9. Rule Engine

The `RuleEngine` is responsible for evaluating all configured rules against a `CreditPosition`.

Its responsibilities are:

1. receive the credit position;
2. execute the configured rules;
3. collect the resulting `RuleResult` objects;
4. return the complete set of rule evaluations.

Conceptually:

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

An important architectural invariant is:

> **The rule engine produces one `RuleResult` for every configured rule.**

Therefore:

```text
len(assessment.rule_results)
    =
len(rule_engine.rules)
```

This invariant is explicitly verified by the automated test suite.

The rule engine does not:

* invoke an LLM;
* generate natural-language reports;
* determine narrative explanations;
* make decisions outside the configured rule logic.

---

# 10. Assessment Status Calculation

The overall assessment status is calculated by the dedicated `AssessmentStatusCalculator`.

This responsibility is intentionally separated from individual rules.

The architecture is:

```text
RuleResult[]
      │
      ▼
AssessmentStatusCalculator
      │
      ▼
AssessmentStatus
```

The current assessment statuses are:

```text
NORMAL
ATTENTION
CRITICAL
```

The calculator evaluates the collection of deterministic rule results.

A key invariant is:

```text
TRIGGERED rules
        =
rules capable of affecting assessment severity
```

In particular:

```text
NOT_EVALUABLE
```

does not count as a triggered rule.

The current behavior is therefore conceptually:

```text
No triggered rules
        ↓
NORMAL

One triggered rule
        ↓
ATTENTION

Multiple triggered rules
        ↓
CRITICAL
```

The exact aggregation logic remains centralized inside `AssessmentStatusCalculator`.

This prevents individual rules from becoming responsible for the global assessment state.

---

# 11. Assessment Service

`AssessmentService` coordinates the deterministic assessment process.

Its principal responsibilities are:

1. receive a `CreditPosition`;
2. invoke the `RuleEngine`;
3. collect all `RuleResult` objects;
4. generate findings for rules with configured comments;
5. invoke `AssessmentStatusCalculator`;
6. construct the final `Assessment`.

Conceptually:

```text
CreditPosition
      │
      ▼
AssessmentService
      │
      ├──────────────► RuleEngine
      │                    │
      │                    ▼
      │               RuleResult[]
      │
      ├──────────────► CommentEngine
      │                    │
      │                    ▼
      │              RuleFinding[]
      │
      └──────────────► AssessmentStatusCalculator
                           │
                           ▼
                    AssessmentStatus
                           │
                           ▼
                       Assessment
```

The service therefore acts as the main entry point into the deterministic assessment domain.

---

# 12. Finding and Comment Architecture

The assessment layer distinguishes between:

```text
RuleResult
```

and:

```text
RuleFinding
```

A `RuleResult` represents the machine-readable outcome of a rule.

A `RuleFinding` combines the rule result with an optional human-readable comment.

Conceptually:

```text
RuleResult
    │
    ▼
CommentEngine
    │
    ├── Comment exists
    │       ↓
    │   RuleFinding
    │
    └── No comment
            ↓
       No finding
```

This distinction is important because not every triggered rule necessarily has a configured comment.

The assessment therefore preserves the complete rule evaluation set while findings contain only rules for which a corresponding comment is available.

---

## 12.1 Comment Engine

`CommentEngine` maps rule results to configured explanatory comments.

Its responsibility is limited to generating comments associated with known rules.

It does not:

* change rule status;
* change severity;
* change thresholds;
* determine the assessment status.

For example:

```text
RuleResult(R001)
      │
      ▼
CommentEngine
      │
      ▼
Comment(R001)
      │
      ▼
RuleFinding
```

If no comment is configured for a result:

```text
RuleResult
      │
      ▼
CommentEngine
      │
      ▼
None
```

The `AssessmentService` explicitly ignores missing comments when constructing findings.

This behavior is covered by automated tests.

---

# 13. Assessment Object

The resulting `Assessment` represents the deterministic output of the assessment layer.

Conceptually:

```text
Assessment
├── position_id
├── status
├── rule_results[]
└── findings[]
```

The object therefore contains both:

1. the complete set of deterministic rule evaluations;
2. the subset of findings associated with available comments.

The assessment is the authoritative domain object consumed by the subsequent analysis layer.

---

# 14. Analysis Layer

The analysis layer transforms the deterministic `Assessment` into an `AssessmentAnalysis`.

It is implemented through the `AnalysisAgent`.

The analysis agent does not perform an independent credit assessment.

Instead, it structures already-established deterministic information for downstream reporting.

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

The analysis layer is therefore a transformation layer rather than a second decision engine.

---

# 15. Assessment Analysis

`AssessmentAnalysis` acts as the controlled boundary between assessment and reporting.

Conceptually:

```text
AssessmentAnalysis
├── assessment_status
├── key_findings
├── risk_factors
└── limitations
```

The assessment status is propagated from the deterministic assessment.

The structured findings originate from deterministic rule evaluation.

Limitations represent information that is unavailable or cannot be evaluated reliably.

The analysis object therefore provides the reporting layer with a controlled representation of the assessment.

---

# 16. Information Ownership

Each architectural layer owns a different category of information.

```text
CreditPosition
    │
    │ Structured financial inputs
    ▼
RuleEngine
    │
    │ Rule evaluations
    ▼
AssessmentService
    │
    │ Status + findings
    ▼
Assessment
    │
    │ Structured assessment
    ▼
AnalysisAgent
    │
    │ Findings + risks + limitations
    ▼
AssessmentAnalysis
    │
    │ Controlled reporting input
    ▼
ReportingAgent
    │
    ▼
Report
```

The critical principle is:

> Information becomes progressively more presentation-oriented, but deterministic assessment information is never delegated to the LLM for reconstruction.

---

# 17. Reporting Architecture

The reporting layer transforms `AssessmentAnalysis` into a final `Report`.

The central coordinator is the `ReportingAgent`.

Two reporting strategies are available:

```text
ReportGenerator
      │
      ├── DeterministicReportGenerator
      │
      └── LLMReportGenerator
```

Both generators consume the same `AssessmentAnalysis`.

This provides reporting substitutability:

```text
AssessmentAnalysis
       │
       ├── Deterministic reporting
       │
       └── LLM-assisted reporting
```

The assessment and analysis layers remain unchanged.

---

# 18. Reporting Agent

The `ReportingAgent` coordinates report generation.

Its responsibilities include:

* selecting or invoking the configured report generator;
* handling generation failures;
* invoking the fallback generator where required;
* exposing basic runtime diagnostics.

Conceptually:

```text
ReportingAgent
      │
      ▼
Primary Generator
      │
      ├── Success ─────► Report
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

```text
Report orchestration
```

from:

```text
Report generation
```

---

# 19. Deterministic Report Generator

`DeterministicReportGenerator` produces a report without requiring an external LLM.

Its purpose is to provide:

* predictable output;
* offline execution;
* testability;
* a reliable fallback;
* a baseline for comparison with generated reporting.

The generator consumes the same deterministic `AssessmentAnalysis` used by the LLM reporting path.

Therefore:

```text
AssessmentAnalysis
       │
       ▼
DeterministicReportGenerator
       │
       ▼
Report
```

This guarantees that report generation remains possible even when external generative services are unavailable.

---

# 20. LLM Report Generator

`LLMReportGenerator` provides the generative reporting implementation.

Its responsibility is intentionally narrow:

> Generate a natural-language executive summary from the structured `AssessmentAnalysis`.

The processing sequence is:

```text
AssessmentAnalysis
      │
      ▼
LLMReportGenerator
      │
      ▼
Prompt Construction
      │
      ▼
LLMClient.generate()
      │
      ▼
Response Validation
      │
      ▼
Report
```

The LLM is not responsible for reconstructing:

* assessment status;
* rule findings;
* risk factors;
* limitations.

Those elements originate from the deterministic pipeline.

The LLM primarily contributes the narrative executive summary.

---

# 21. Controlled LLM Prompt

The prompt constructed by `LLMReportGenerator` provides the model with already-validated assessment information.

The prompt is designed to constrain the model to:

* use only supplied information;
* avoid unsupported financial facts;
* avoid inventing causes or trends;
* preserve the assessment status;
* avoid making independent credit decisions;
* avoid unsupported recommendations;
* distinguish findings from limitations;
* avoid inferring missing information;
* use professional credit-risk terminology.

The prompt is an important safety mechanism, but it is not considered a sufficient technical guarantee by itself.

LLM output is therefore validated before acceptance.

---

# 22. LLM Response Validation

LLM output is treated as **untrusted generated content**.

The reporting layer validates the generated response before constructing the final report.

The current validation process includes checks such as:

```text
LLM Response
      │
      ▼
Non-empty?
      │
      ▼
Expected assessment status present?
      │
      ▼
Valid Response
```

Invalid responses trigger the fallback mechanism.

Examples include:

```text
Empty response
      ↓
Validation failure
      ↓
Deterministic fallback
```

and:

```text
Expected assessment status missing
      ↓
Validation failure
      ↓
Deterministic fallback
```

The key architectural principle is:

> The system never treats an arbitrary LLM response as an authoritative representation of the assessment.

---

# 23. LLM Client Abstraction

The LLM integration is isolated behind the `LLMClient` abstraction.

The reporting layer therefore depends on:

```text
LLMClient
```

rather than directly on:

```text
GeminiClient
```

Conceptually:

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

This follows the Dependency Inversion Principle and provides provider independence.

Potential future implementations include:

```text
OpenAIClient
LocalLLMClient
OtherProviderClient
```

without requiring changes to `LLMReportGenerator`.

---

# 24. Mock LLM Client

`MockLLMClient` provides deterministic LLM behavior for automated testing.

It avoids dependencies on:

* network connectivity;
* external API availability;
* API quotas;
* API costs;
* model stochasticity.

This allows the LLM reporting layer to be tested as a normal application component.

The mock can also expose the generated prompt to tests, allowing prompt construction to be verified independently from external model execution.

---

# 25. Gemini Client

`GeminiClient` provides the concrete integration with the Gemini API.

Provider-specific implementation details remain isolated inside this component.

The application therefore follows:

```text
Application
    ↓
LLMClient
    ↓
GeminiClient
    ↓
Gemini API
```

rather than coupling the entire application directly to the provider.

Real Gemini calls are intentionally separated from the automated test suite.

---

# 26. Fallback Architecture

The reporting architecture implements graceful degradation.

The intended configuration is:

```text
Primary:
LLMReportGenerator

Fallback:
DeterministicReportGenerator
```

The execution path is:

```text
                    ReportingAgent
                          │
                          ▼
                 LLMReportGenerator
                          │
                     generate()
                          │
              ┌───────────┴───────────┐
              │                       │
           success                 failure
              │                       │
              ▼                       ▼
        Validate response      Record failure
              │                       │
              │                       ▼
              │             DeterministicReportGenerator
              │                       │
              └───────────┬───────────┘
                          ▼
                        Report
```

Possible failure conditions include:

* LLM client exception;
* API authentication failure;
* API quota exhaustion;
* service unavailability;
* timeout;
* empty response;
* failed response validation.

The fallback consumes the same deterministic `AssessmentAnalysis`.

Therefore:

```text
LLM Failure
    ≠
Assessment Failure
```

---

# 27. Reporting Diagnostics

The `ReportingAgent` maintains runtime diagnostics such as:

```text
last_generator_used
last_error
```

These attributes provide basic observability of the reporting path.

For example:

```text
last_generator_used = PRIMARY
```

indicates that the primary generator successfully produced the report.

Whereas:

```text
last_generator_used = FALLBACK
```

indicates that the deterministic fallback was used.

`last_error` can preserve a concise description of the failure that caused fallback activation.

This allows the application and tests to distinguish:

```text
Successful LLM reporting
```

from:

```text
Successful deterministic fallback
```

---

# 28. Workflow Architecture

`AssessmentWorkflow` coordinates the three principal processing stages:

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

```text
assessment
analysis
report
```

Keeping all three intermediate results observable is important for:

* testing;
* debugging;
* explainability;
* future application integration.

---

# 29. Application-Level Orchestration

The `Orchestrator` provides an application-level entry point for executing the complete workflow.

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

The orchestrator hides internal component construction from the application caller.

This reduces coupling between the application entry point and the individual implementation classes.

---

# 30. Factory Pattern and Dependency Injection

The project uses factories to centralize dependency construction.

For example:

```text
create_default_assessment_service()
```

constructs the default deterministic assessment service from:

```text
RuleEngine(get_default_rules())
CommentEngine()
AssessmentStatusCalculator()
```

Conceptually:

```text
create_default_assessment_service()
            │
            ├── get_default_rules()
            │       ↓
            │   RuleEngine
            │
            ├── CommentEngine
            │
            └── AssessmentStatusCalculator
                    │
                    ▼
             AssessmentService
```

This architecture makes dependencies explicit and allows unit tests to inject mocks directly.

For example:

```text
AssessmentService
      │
      ├── Mock RuleEngine
      ├── Mock CommentEngine
      └── Mock Status Calculator
```

This is particularly important for testing service orchestration independently from the underlying rule implementation.

---

# 31. Dependency Injection

The application uses constructor-based dependency injection.

For example, `AssessmentService` receives:

```text
RuleEngine
CommentEngine
AssessmentStatusCalculator
```

rather than constructing them internally.

This provides:

* loose coupling;
* easier unit testing;
* explicit dependencies;
* replaceability of implementations.

The same principle applies to reporting and LLM components.

---

# 32. Separation of Responsibilities

The main responsibilities are summarized below.

| Component                      | Responsibility                                   |
| ------------------------------ | ------------------------------------------------ |
| `CreditPosition`               | Represents structured financial input            |
| Rule implementations           | Evaluate individual financial conditions         |
| `RuleConfig`                   | Defines configurable rule parameters             |
| `SeverityThreshold`            | Defines severity-specific thresholds             |
| `RuleEngine`                   | Executes all configured rules                    |
| `RuleResult`                   | Represents an individual rule evaluation         |
| `CommentEngine`                | Maps rule results to configured comments         |
| `RuleFinding`                  | Combines a rule result with its comment          |
| `AssessmentStatusCalculator`   | Determines the overall assessment status         |
| `AssessmentService`            | Coordinates deterministic assessment             |
| `Assessment`                   | Represents the complete deterministic assessment |
| `AnalysisAgent`                | Structures assessment information for reporting  |
| `AssessmentAnalysis`           | Represents structured analysis                   |
| `ReportingAgent`               | Coordinates report generation and fallback       |
| `ReportGenerator`              | Defines report-generation abstraction            |
| `DeterministicReportGenerator` | Generates deterministic reports                  |
| `LLMReportGenerator`           | Generates the narrative executive summary        |
| `LLMClient`                    | Abstracts communication with an LLM              |
| `MockLLMClient`                | Provides deterministic LLM behavior for tests    |
| `GeminiClient`                 | Provides Gemini integration                      |
| `Report`                       | Represents the final report                      |
| `AssessmentWorkflow`           | Coordinates assessment, analysis, and reporting  |
| `Orchestrator`                 | Provides application-level workflow execution    |
| Factory functions              | Centralize dependency construction               |

---

# 33. Deterministic–Generative Boundary

The most important architectural boundary is between the deterministic domain and the generative reporting layer.

```text
┌─────────────────────────────────────────────────────────┐
│                  DETERMINISTIC DOMAIN                   │
│                                                         │
│ CreditPosition                                          │
│       ↓                                                 │
│ Rules                                                   │
│       ↓                                                 │
│ RuleEngine                                              │
│       ↓                                                 │
│ RuleResult[]                                            │
│       ↓                                                 │
│ AssessmentStatusCalculator                              │
│       ↓                                                 │
│ CommentEngine                                           │
│       ↓                                                 │
│ Assessment                                              │
│       ↓                                                 │
│ AnalysisAgent                                           │
│       ↓                                                 │
│ AssessmentAnalysis                                      │
│                                                         │
│                 SOURCE OF TRUTH                         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ Controlled structured data
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    REPORTING DOMAIN                     │
│                                                         │
│ ReportingAgent                                          │
│       │                                                 │
│       ├── DeterministicReportGenerator                  │
│       │                                                 │
│       └── LLMReportGenerator                            │
│                    │                                    │
│                    ▼                                    │
│                LLMClient                                │
│                    │                                    │
│                    ▼                                    │
│              External LLM                               │
│                                                         │
│             NARRATIVE GENERATION                        │
└─────────────────────────────────────────────────────────┘
```

The dependency is intentionally unidirectional:

```text
Deterministic Domain
        │
        ▼
Reporting Domain
        │
        ▼
LLM
```

There is no feedback path from the LLM into the deterministic assessment engine.

---

# 34. Information Preservation Guarantees

The architecture is designed to preserve deterministic information across the complete workflow.

## 34.1 Assessment Status

The following relationship must remain consistent:

```text
Assessment.status
        =
AssessmentAnalysis.assessment_status
        =
Report.assessment_status
```

The LLM does not establish this value.

---

## 34.2 Rule Results

The assessment contains one result for every configured rule:

```text
Configured Rules
      ↓
RuleResult[]
      ↓
Assessment.rule_results
```

This invariant is verified through automated tests.

---

## 34.3 Findings

Findings originate from deterministic rule results and comments.

```text
RuleResult
      ↓
CommentEngine
      ↓
RuleFinding
      ↓
Assessment.findings
```

The LLM does not reconstruct findings from natural language.

---

## 34.4 Limitations

Limitations identified by the deterministic analysis remain controlled by the analysis layer.

The LLM can communicate limitations but does not redefine them.

---

# 35. Testing Architecture

Testing is organized according to architectural responsibility.

The test suite includes:

```text
Unit Tests
    ↓
Integration Tests
    ↓
Workflow / End-to-End Tests
    ↓
Manual Real-LLM Validation
```

Each level verifies different properties.

---

# 36. Unit Testing

Unit tests verify individual components in isolation.

The current suite covers areas including:

* domain models;
* assessment status;
* rule implementations;
* rule configuration;
* rule discovery;
* rule registry;
* rule engine;
* assessment status calculator;
* assessment service;
* comment engine;
* analysis agent;
* reporting components;
* LLM abstractions.

Mocks are used where a test is intended to verify orchestration rather than implementation details.

For example, the `AssessmentService` can be tested with:

```text
MagicMock RuleEngine
MagicMock CommentEngine
MagicMock AssessmentStatusCalculator
```

This allows the test to verify that dependencies are invoked correctly.

---

# 37. Assessment Status Tests

The `AssessmentStatusCalculator` is tested against representative rule-result combinations.

Important cases include:

```text
[]
    ↓
NORMAL
```

```text
NOT_TRIGGERED
NOT_TRIGGERED
    ↓
NORMAL
```

```text
NOT_EVALUABLE
NOT_EVALUABLE
    ↓
NORMAL
```

```text
TRIGGERED
    ↓
ATTENTION
```

```text
TRIGGERED
NOT_EVALUABLE
    ↓
ATTENTION
```

```text
TRIGGERED
TRIGGERED
    ↓
CRITICAL
```

These tests explicitly verify that `NOT_EVALUABLE` results do not incorrectly count as triggered rules.

---

# 38. Assessment Service Tests

`AssessmentService` tests verify both its business behavior and its dependency orchestration.

Representative scenarios include:

* critical assessment;
* normal assessment;
* assessment with non-evaluable rules;
* attention assessment;
* dependency injection;
* correct propagation of rule results;
* correct generation of findings;
* missing comments.

The tests verify relationships such as:

```text
finding.result.rule_id
        =
triggered result.rule_id
```

and:

```text
finding.comment.rule_id
        =
finding.result.rule_id
```

when a comment is available.

They also verify that a missing comment does not cause the complete assessment process to fail.

---

# 39. Factory and Integration Tests

The default factory path is tested separately from isolated dependency-injection tests.

For example:

```text
create_default_assessment_service()
        ↓
RuleEngine(get_default_rules())
        ↓
AssessmentService
        ↓
CreditPosition
        ↓
Assessment
```

These tests verify that the real configured components work together correctly.

This distinction is important:

```text
Unit Test
    =
Does this component behave correctly in isolation?

Integration Test
    =
Do the configured components work correctly together?
```

---

# 40. Shared Pytest Fixtures

The test suite uses `pytest` fixtures to avoid duplicating common dependency construction.

The shared `assessment_service` fixture is defined in `tests/conftest.py`.

Conceptually:

```text
tests/conftest.py
        │
        ▼
assessment_service fixture
        │
        ├── RuleEngine(get_default_rules())
        ├── CommentEngine()
        └── AssessmentStatusCalculator()
        │
        ▼
AssessmentService
```

Tests that declare:

```python
def test_something(assessment_service):
    ...
```

automatically receive the configured fixture.

The fixture is therefore **test infrastructure**, not production application code.

Its purpose is to provide a consistent default service configuration across multiple test modules.

---

# 41. Integration Testing

Integration tests verify interactions between multiple real components.

Examples include:

```text
AssessmentService
      +
RuleEngine
      +
CommentEngine
      +
AssessmentStatusCalculator
```

and:

```text
Assessment
      +
AnalysisAgent
      +
ReportingAgent
```

Integration tests are particularly important because many architectural guarantees depend on the interaction between components rather than on individual methods.

---

# 42. End-to-End Workflow Testing

End-to-end tests execute the complete pipeline:

```text
CreditPosition
      ↓
Assessment
      ↓
AssessmentAnalysis
      ↓
Report
```

These tests verify that deterministic information survives the complete workflow.

Important invariants include:

```text
Assessment.status
        =
Analysis.assessment_status
        =
Report.assessment_status
```

and:

```text
Deterministic Findings
        ↓
Analysis
        ↓
Report
```

---

# 43. LLM Testing

Automated tests do not depend on the real Gemini API.

Instead:

```text
LLMReportGenerator
        ↓
MockLLMClient
```

is used for deterministic testing.

Representative scenarios include:

* valid LLM response;
* empty response;
* missing assessment status;
* client exception;
* invalid response;
* deterministic fallback;
* preservation of deterministic findings;
* preservation of limitations.

This makes the LLM integration testable without external infrastructure.

---

# 44. Real LLM Validation

Real Gemini calls are treated as integration validation rather than as standard unit tests.

The purpose is to verify:

* actual provider connectivity;
* prompt compatibility;
* model response behavior;
* response validation;
* fallback behavior against a real service.

Representative assessment scenarios include:

```text
NORMAL
ATTENTION
CRITICAL
```

The real LLM therefore validates the generative component, while the automated test suite remains deterministic and reproducible.

---

# 45. Quality and Static Analysis

The repository uses automated quality tools.

The test suite can be executed with:

```powershell
python -m pytest
```

Static analysis is performed using:

```powershell
python -m ruff check .
```

Coverage can be evaluated with:

```powershell
python -m pytest --cov=src --cov-report=term-missing
```

These checks are intended to identify:

* functional regressions;
* unused imports;
* code-quality issues;
* insufficient test coverage;
* inconsistencies introduced during refactoring.

The project therefore treats testing and static analysis as part of the architectural development process rather than as separate activities.

---

# 46. Continuous Integration

GitHub Actions provides automated validation of repository changes.

The CI pipeline is designed to verify that changes preserve the expected quality of the project.

Typical validation includes:

```text
Code Change
    │
    ▼
GitHub Actions
    │
    ├── Ruff
    │
    └── Pytest
         │
         ▼
      Validation
```

Real external LLM calls are intentionally excluded from the standard CI path so that CI remains deterministic and does not depend on API credentials or external service availability.

---

# 47. Architectural Invariants

The architecture establishes several important invariants.

## Invariant 1 — Deterministic Assessment Authority

```text
Assessment status
```

is determined exclusively by the deterministic assessment layer.

---

## Invariant 2 — Complete Rule Evaluation

For every assessment:

```text
number of rule results
=
number of configured rules
```

---

## Invariant 3 — Non-Evaluable Rules Are Not Triggered

```text
NOT_EVALUABLE
    ≠
TRIGGERED
```

Non-evaluable rules do not independently increase assessment severity.

---

## Invariant 4 — Status Preservation

```text
Assessment.status
    =
AssessmentAnalysis.assessment_status
    =
Report.assessment_status
```

---

## Invariant 5 — Finding Traceability

Every finding is traceable to its underlying deterministic rule result.

```text
RuleFinding.result
        ↓
RuleResult
        ↓
Rule
```

---

## Invariant 6 — LLM Isolation

The LLM cannot modify:

```text
RuleResult
AssessmentStatus
RuleSeverity
Thresholds
Findings
Limitations
```

---

## Invariant 7 — Reporting Resilience

An LLM failure must not invalidate the deterministic assessment.

```text
LLM failure
    ↓
Deterministic fallback
```

---

## Invariant 8 — Provider Independence

Changing the LLM provider must not require changes to:

```text
AssessmentService
RuleEngine
Rules
AssessmentStatusCalculator
AnalysisAgent
```

---

# 48. Error Boundaries

The architecture isolates errors according to their responsibility.

```text
Rule Error
    ↓
Assessment Domain

Analysis Error
    ↓
Analysis Domain

LLM Error
    ↓
Reporting Domain
    ↓
Fallback
```

This prevents failures from propagating unnecessarily across unrelated layers.

In particular:

```text
LLM Error
    X
    │
    └──► Deterministic Assessment
```

The LLM cannot retroactively alter the assessment.

---

# 49. Architectural Rationale

A fully LLM-driven credit assessment could introduce undesirable characteristics into a process that benefits from deterministic business logic:

* non-deterministic outcomes;
* limited reproducibility;
* difficulty in tracing decisions;
* sensitivity to prompt changes;
* model-dependent behavior;
* difficulty validating thresholds and severity;
* external service dependency.

The project therefore adopts:

```text
Deterministic Assessment
          +
Structured Analysis
          +
Generative Reporting
```

The deterministic layer provides:

* reproducibility;
* explicit business logic;
* traceability;
* controlled severity;
* controlled thresholds;
* testability.

The generative layer provides:

* natural-language communication;
* executive-summary generation;
* flexible presentation.

The two layers are complementary rather than interchangeable.

---

# 50. Current Architectural Scope

The current architecture includes:

```text
✓ Structured CreditPosition domain model
✓ Deterministic rule engine
✓ Configurable rule definitions
✓ Rule discovery and registry
✓ Explicit RuleStatus
✓ Explicit RuleSeverity
✓ RuleResult model
✓ AssessmentStatusCalculator
✓ AssessmentService
✓ CommentEngine
✓ RuleFinding
✓ Assessment model
✓ AnalysisAgent
✓ AssessmentAnalysis
✓ ReportingAgent
✓ ReportGenerator abstraction
✓ DeterministicReportGenerator
✓ LLMReportGenerator
✓ LLMClient abstraction
✓ MockLLMClient
✓ GeminiClient
✓ LLM response validation
✓ Deterministic fallback
✓ AssessmentWorkflow
✓ Orchestrator
✓ Factory-based dependency construction
✓ Unit tests
✓ Integration tests
✓ Workflow tests
✓ Shared pytest fixtures
✓ Ruff static analysis
✓ Coverage analysis
✓ GitHub Actions CI
✓ Real Gemini validation
```

---

# 51. Future Extension Points

The architecture provides several natural extension points.

## 51.1 Additional Rules

New rules can be introduced independently:

```text
New Rule
    ↓
Rule Registry
    ↓
RuleEngine
    ↓
AssessmentService
```

The analysis and reporting layers do not need to be redesigned.

---

## 51.2 Additional LLM Providers

New providers can implement:

```text
LLMClient
```

For example:

```text
LLMClient
    ├── GeminiClient
    ├── MockLLMClient
    ├── OpenAIClient
    └── LocalLLMClient
```

---

## 51.3 Local LLM

A local model can be integrated behind the same abstraction:

```text
LLMReportGenerator
        │
        ▼
    LLMClient
        │
        └── LocalLLMClient
```

This would allow experimentation with locally hosted models while preserving the deterministic assessment boundary.

---

## 51.4 Structured LLM Output

The reporting layer could evolve from free-form executive summaries toward schema-constrained output.

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

The generated structure could then be compared against `AssessmentAnalysis`.

---

## 51.5 Stronger Semantic Validation

Future validation could detect:

* unsupported claims;
* contradictions;
* missing findings;
* inconsistent financial values;
* unsupported causal explanations;
* unsupported recommendations.

Such validation would strengthen the existing deterministic–generative boundary.

---

## 51.6 Application Interfaces

Future iterations could expose the workflow through:

```text
REST API
      │
      ▼
Orchestrator
      │
      ▼
AssessmentWorkflow
```

A web interface could then consume the same application-level orchestration without modifying the deterministic domain.

---

# 52. Summary

The `credit-assessment-system` implements a controlled hybrid architecture:

```text
CreditPosition
      │
      ▼
Deterministic Rule Engine
      │
      ▼
RuleResult[]
      │
      ├── Status Calculation
      └── Finding Generation
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
      ├───────────────────┐
      ▼                   ▼
LLM Reporting       Deterministic Reporting
      │                   │
      └─────────┬─────────┘
                ▼
              Report
```

The central architectural guarantee is:

> **The deterministic assessment engine remains the authoritative source of truth, while the LLM is restricted to controlled natural-language reporting.**

The architecture therefore provides a clear separation between:

```text
WHAT THE SYSTEM DECIDES
        │
        ▼
Deterministic Assessment
```

and:

```text
HOW THE SYSTEM COMMUNICATES IT
        │
        ▼
Deterministic or LLM Reporting
```

This separation is reinforced not only by the class structure, but also by explicit data contracts, dependency injection, factory-based construction, unit tests, integration tests, workflow tests, LLM mocks, response validation, and deterministic fallback.

The result is an architecture in which generative AI is **LLM-assisted rather than LLM-driven**: the model can improve the communication of an assessment, but it cannot become the authority responsible for producing that assessment.
