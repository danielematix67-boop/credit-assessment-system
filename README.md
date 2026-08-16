# Credit Assessment System

A modular, deterministic credit assessment prototype with a multi-agent workflow and an optional LLM-powered reporting layer.

The system is designed around a strict separation between **credit decision logic** and **natural-language generation**:

> **Deterministic rules determine the assessment. Agents structure and orchestrate the analysis. The LLM supports natural-language reporting.**

The LLM is therefore **not part of the credit decision-making process**.

Assessment status, rule outcomes, thresholds, severity, findings, and limitations are established by the deterministic layer before the reporting stage.

The project is intended as a technical prototype and academic laboratory for demonstrating how traditional rule-based credit assessment can be combined with modern software architecture, agent-based orchestration, and controlled generative AI.

---

# 1. Project Overview

The `credit-assessment-system` implements a complete credit assessment workflow starting from a structured financial position and ending with a structured credit report.

The system combines:

* deterministic business rules;
* configurable thresholds and severity policies;
* rule discovery and registration;
* structured domain models;
* an assessment service;
* an analysis agent;
* a reporting agent;
* deterministic and LLM-based report generators;
* provider-independent LLM integration;
* LLM response validation;
* deterministic fallback mechanisms;
* automated unit and integration testing;
* static analysis;
* continuous integration.

The central architectural principle is:

```text
                    CREDIT ASSESSMENT WORKFLOW

                         CreditPosition
                               │
                               ▼
                       AssessmentService
                               │
                               ▼
                         RuleEngine
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
                 Rules              RuleResult[]
                    │                     │
                    └──────────┬──────────┘
                               ▼
                  AssessmentStatusCalculator
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
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
     DeterministicReportGenerator      LLMReportGenerator
                                              │
                                              ▼
                                          LLMClient
                                              │
                                    ┌─────────┴─────────┐
                                    │                   │
                                    ▼                   ▼
                                  Gemini               Mock
                                    │
                                    └─────────┬─────────┘
                                              ▼
                                            Report
```

The reporting mechanism can therefore evolve without changing the underlying credit assessment logic.

---

# 2. Core Architectural Principle

The most important design decision is the separation between **assessment authority** and **language generation**.

```text
┌──────────────────────────────────────────────────────────┐
│                 DETERMINISTIC LAYER                      │
│                                                          │
│  Rules → Thresholds → Severity → Findings → Status      │
│                                                          │
│                  SOURCE OF TRUTH                         │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                        │
│                                                          │
│              Assessment → Analysis                       │
│                                                          │
│         Structured interpretation of results             │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   REPORTING LAYER                        │
│                                                          │
│       Deterministic Generator / LLM Generator            │
│                                                          │
│             Natural-language communication               │
└──────────────────────────────────────────────────────────┘
```

The system is therefore:

> **LLM-assisted, not LLM-driven.**

The LLM cannot redefine the result produced by the deterministic assessment engine.

---

# 3. Architectural Guarantees

The architecture is designed to preserve several invariants throughout the complete workflow.

## 3.1 Assessment Authority

The final assessment status is calculated exclusively by the deterministic layer.

```text
RuleResult[]
      │
      ▼
AssessmentStatusCalculator
      │
      ▼
Assessment.status
```

The LLM does not participate in this calculation.

---

## 3.2 Status Preservation

The assessment status must remain consistent throughout the pipeline:

```text
Assessment.status
        =
AssessmentAnalysis.assessment_status
        =
Report.assessment_status
```

The reporting layer cannot replace the deterministic status with a value generated by the LLM.

---

## 3.3 Finding Preservation

Findings originate from deterministic rule evaluation.

The LLM may describe or summarize them, but it does not create an independent set of credit findings.

```text
RuleResult
    ↓
RuleFinding
    ↓
Assessment
    ↓
AssessmentAnalysis
    ↓
Report
```

---

## 3.4 Limitation Preservation

A rule that cannot be evaluated is represented explicitly as:

```text
NOT_EVALUABLE
```

Such rules are treated as limitations rather than as negative findings.

The information is preserved through the analysis and reporting layers.

---

## 3.5 LLM Isolation

An LLM failure cannot change the deterministic assessment.

```text
LLM failure
     │
     ▼
Deterministic fallback
     │
     ▼
Report
```

Therefore:

> **LLM availability is not a prerequisite for credit assessment.**

---

## 3.6 Reporting Substitutability

The reporting implementation can be changed without modifying the assessment engine:

```text
ReportGenerator
      │
      ├── DeterministicReportGenerator
      │
      └── LLMReportGenerator
```

This follows the Dependency Inversion Principle and allows different reporting strategies to be introduced independently.

---

# 4. System Architecture

The application is organized into several logical layers.

```text
┌───────────────────────────────────────────────────────┐
│                 ORCHESTRATION                         │
│                                                       │
│          AssessmentOrchestrator                       │
│                       │                               │
│                       ▼                               │
│               AssessmentWorkflow                      │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│                  ASSESSMENT                            │
│                                                       │
│ AssessmentService → RuleEngine → Rules                │
│                          │                            │
│                          ▼                            │
│                     RuleResult[]                       │
│                          │                            │
│                          ▼                            │
│              AssessmentStatusCalculator                │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│                    ANALYSIS                            │
│                                                       │
│                   AnalysisAgent                       │
│                          │                            │
│                          ▼                            │
│              AssessmentAnalysis                        │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│                   REPORTING                            │
│                                                       │
│                   ReportingAgent                      │
│                          │                            │
│              ┌───────────┴───────────┐                │
│              ▼                       ▼                │
│       Deterministic             LLM Generator         │
│       Generator                       │               │
│                                       ▼               │
│                                  LLM Client            │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
                      Report
```

---

# 5. Domain Model

The system uses explicit domain objects to represent the state of the assessment.

The main objects are:

```text
CreditPosition
      │
      ▼
RuleResult[]
      │
      ▼
Assessment
      │
      ▼
AssessmentAnalysis
      │
      ▼
Report
```

This explicit data flow makes the system easier to reason about, test, and audit.

---

## 5.1 CreditPosition

`CreditPosition` represents the financial information associated with a credit position.

The current domain model includes indicators such as:

* revenue;
* revenue growth;
* change in finished goods inventory;
* operating grants;
* net purchases;
* change in raw materials inventory;
* costs for services and third-party assets;
* personnel costs;
* operating value added;
* gross operating margin;
* depreciation of tangible assets;
* working capital impairments;
* operating provisions;
* net operating margin;
* other income/expenses balance;
* EBITDA;
* profit/loss;
* EBITDA margin;
* PFN-to-EBITDA;
* interest expense.

The model supports optional fields where an indicator may be unavailable.

For example:

```python
CreditPosition(
    position_id="POS001",
    revenue_growth=-0.15,
    ebitda=-50000,
    ebitda_margin=-0.05,
    pfn_to_ebitda=6.0,
)
```

Optional values are represented explicitly as `None`.

This allows the rule engine to distinguish between:

```text
Value available
        │
        ├── evaluate normally
        │
Value unavailable
        │
        └── NOT_EVALUABLE
```

---

# 6. Deterministic Assessment Layer

The deterministic assessment layer is the **authoritative decision-making component**.

Its principal components are:

* `CreditPosition`;
* `RuleConfig`;
* `SeverityPolicy`;
* individual rules;
* `RuleRegistry`;
* `RuleEngine`;
* `AssessmentService`;
* `AssessmentStatusCalculator`;
* `Assessment`;
* `RuleResult`;
* `RuleFinding`.

---

# 7. Rule Architecture

Rules implement a common `Rule` abstraction.

A rule receives a `CreditPosition` and produces a `RuleResult`.

Conceptually:

```text
CreditPosition
      │
      ▼
     Rule
      │
      ▼
 RuleResult
```

A `RuleResult` contains structured information such as:

```python
RuleResult(
    rule_id="R001",
    rule_name="Revenue growth deterioration",
    category="revenue",
    status=RuleStatus.TRIGGERED,
    value=-0.15,
    threshold=-0.10,
    severity=RuleSeverity.MEDIUM,
)
```

This makes each rule evaluation explicit and traceable.

---

# 8. Rule Status

The rule engine distinguishes three fundamental evaluation states:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

## TRIGGERED

The rule condition has been met.

Example:

```text
Revenue growth = -15%
Threshold       = -10%

-15% ≤ -10%
       ↓
TRIGGERED
```

---

## NOT_TRIGGERED

The indicator is available and does not breach the configured rule condition.

---

## NOT_EVALUABLE

The required information is unavailable.

For example:

```text
revenue_growth = None
```

The rule is not treated as triggered.

This distinction is particularly important in credit assessment because:

```text
Missing information
        ≠
Negative information
```

---

# 9. Rule Severity

Triggered rules are associated with explicit severity levels:

```text
LOW
MEDIUM
HIGH
```

Severity is determined by the deterministic configuration.

It is never inferred by the LLM.

The severity mechanism supports both:

```text
HIGHER_IS_WORSE
```

and:

```text
LOWER_IS_WORSE
```

This allows rules to represent indicators where either increasing or decreasing values correspond to worsening credit conditions.

---

# 10. Severity Policy

Severity resolution is encapsulated through a dedicated `SeverityPolicy`.

A policy contains:

```text
Direction
    +
Thresholds
    +
Severity levels
```

For example:

```text
LOWER_IS_WORSE

0.10 → LOW
0.05 → MEDIUM
0.00 → HIGH
```

The policy evaluates a value against the configured thresholds and returns the highest severity reached.

Boundary values are inclusive.

For example:

```text
0.10 → LOW
0.05 → MEDIUM
0.00 → HIGH
```

For a `HIGHER_IS_WORSE` policy:

```text
3.0 → LOW
4.0 → MEDIUM
5.0 → HIGH
```

If no threshold is reached, the policy returns `None` and the rule can use its configured default severity.

This mechanism is independently unit-tested.

---

# 11. Rule Configuration

Rule execution is separated from rule configuration.

`RuleConfig` contains the business parameters required by a rule.

Typical configuration includes:

```text
rule_id
rule_name
category
threshold
severity
severity_direction
severity_thresholds
```

The configuration is immutable.

This prevents runtime modification of business parameters after rule construction.

Conceptually:

```text
Configuration
      │
      ▼
Immutable RuleConfig
      │
      ▼
Rule
      │
      ▼
RuleResult
```

---

# 12. YAML-Based Configuration

The current rule configuration is externalized in:

```text
config/rules.yaml
```

The configuration currently covers the registered rules:

```text
R001
R002
R003
R004
R005
R006
R007
```

The YAML configuration is loaded by:

```text
RuleConfigLoader
```

and transformed into immutable `RuleConfig` objects.

This provides a separation between:

```text
Business parameters
        │
        ▼
Configuration
        │
        ▼
Rule implementation
```

The approach makes threshold and severity changes easier to manage and test.

---

# 13. Current Rule Set

The current prototype includes seven registered rules.

| Rule | Category      | Indicator                    |
| ---- | ------------- | ---------------------------- |
| R001 | Revenue       | Revenue growth deterioration |
| R002 | Profitability | Negative EBITDA              |
| R003 | Profitability | EBITDA margin                |
| R004 | Leverage      | PFN / EBITDA                 |
| R005 | Profitability | Interest expense / EBITDA    |
| R006 | Profitability | Inventory-supported EBITDA   |
| R007 | Leverage      | Interest coverage            |

The exact thresholds and severity policies are maintained in:

```text
config/rules.yaml
```

This avoids duplicating business parameters between source code and documentation.

---

# 14. Rule Discovery and Registry

The project separates rule implementation from rule discovery and rule instantiation.

The discovery mechanism:

```text
discover_rules()
      │
      ▼
Rule registry
      │
      ▼
Registered rule classes
```

The registry currently contains:

```text
R001
R002
R003
R004
R005
R006
R007
```

Discovery is designed to be idempotent.

Calling:

```python
discover_rules()
```

multiple times does not change the resulting registry.

This behavior is explicitly covered by the test suite.

---

# 15. Rule Registry and Factory

The rule registry provides two principal capabilities.

## Registered Rule Lookup

A rule can be retrieved using its identifier:

```python
Rule.get_registered_rule("R001")
```

Unknown identifiers raise an explicit error:

```text
ValueError: Unknown rule_id: ...
```

---

## Rule Construction

`build_rules()` creates rule instances from a collection of `RuleConfig` objects.

The implementation guarantees:

* configuration order is preserved;
* the supplied configuration object is preserved;
* unknown rule IDs are rejected;
* each invocation creates independent rule instances.

For example:

```text
configs
   │
   ▼
build_rules()
   │
   ├── R004
   ├── R001
   └── R002
```

The resulting rule order remains:

```text
R004
R001
R002
```

This behavior is explicitly tested.

---

# 16. Rule Engine

The `RuleEngine` executes the configured rules against a `CreditPosition`.

```text
CreditPosition
      │
      ▼
RuleEngine
      │
      ├── R001
      ├── R002
      ├── R003
      ├── R004
      ├── R005
      ├── R006
      └── R007
      │
      ▼
RuleResult[]
```

The engine provides the complete deterministic rule evaluation set.

The assessment layer does not depend on an LLM to interpret rule outcomes.

---

# 17. RuleResult

`RuleResult` is an immutable representation of a rule evaluation.

It contains:

```text
rule_id
rule_name
category
status
value
threshold
severity
```

Immutability is important because a rule result becomes part of the assessment's traceable decision record.

Once generated, downstream components should consume the result rather than modify it.

---

# 18. Assessment Status

The final assessment status is calculated independently from individual rule implementation details.

The current status model is:

```text
NORMAL
ATTENTION
CRITICAL
```

The `AssessmentStatusCalculator` applies the deterministic aggregation logic to the collection of `RuleResult` objects.

The current behavior is:

```text
No triggered rules
        ↓
NORMAL
```

```text
One triggered rule
        ↓
ATTENTION
```

```text
Multiple triggered rules
        ↓
CRITICAL
```

`NOT_EVALUABLE` results do not count as triggered rules.

Therefore:

```text
TRIGGERED
    → affects assessment status

NOT_TRIGGERED
    → does not affect status

NOT_EVALUABLE
    → does not count as a triggered rule
```

This behavior is covered by dedicated unit tests.

---

# 19. Assessment Service

`AssessmentService` coordinates the deterministic assessment process.

```text
CreditPosition
      │
      ▼
RuleEngine.evaluate()
      │
      ▼
RuleResult[]
      │
      ├───────────────┐
      │               │
      ▼               ▼
CommentEngine   StatusCalculator
      │               │
      ▼               ▼
RuleFinding[]     AssessmentStatus
      │               │
      └───────┬───────┘
              ▼
          Assessment
```

The service is deliberately dependency-injected.

Its principal dependencies are:

```python
AssessmentService(
    rule_engine=...,
    comment_engine=...,
    status_calculator=...,
)
```

This makes the service easy to isolate and test using mocks.

---

# 20. Rule Findings and Comments

Triggered rules can be transformed into structured `RuleFinding` objects.

A finding associates:

```text
RuleResult
    +
Comment
```

The `CommentEngine` maps configured rule IDs to explanatory comments.

If a triggered rule does not have a configured comment, the assessment service does not fail.

Instead, the missing comment is ignored while the underlying deterministic rule result remains part of the assessment.

This provides graceful handling of incomplete reporting metadata.

---

# 21. Analysis Layer

The analysis layer transforms the deterministic assessment into an `AssessmentAnalysis`.

```text
Assessment
    │
    ▼
AnalysisAgent
    │
    ▼
AssessmentAnalysis
```

The analysis agent does not perform an independent credit assessment.

Its purpose is to structure already-determined information for reporting.

The analysis layer can organize:

* assessment status;
* key findings;
* risk factors;
* limitations.

Conceptually:

```text
Triggered findings
        │
        ├──► Key Findings
        │
        └──► High-severity findings
                    │
                    ▼
               Risk Factors

NOT_EVALUABLE rules
        │
        ▼
Limitations
```

---

# 22. Reporting Layer

The reporting layer converts `AssessmentAnalysis` into a final `Report`.

The principal component is the `ReportingAgent`.

It depends on an abstract `ReportGenerator`.

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

This abstraction makes the reporting strategy interchangeable.

---

# 23. Report Model

`Report` is the final structured output of the workflow.

It contains information such as:

```text
position_id
assessment_status
executive_summary
findings_by_category
limitations
```

The report is treated as a domain-level output rather than as raw text.

This distinction is important because:

```text
Executive summary
    → generated natural language

Assessment status
    → deterministic domain value

Findings
    → deterministic domain information

Limitations
    → deterministic domain information
```

The report therefore combines generated language with authoritative structured data.

---

# 24. Deterministic Report Generator

`DeterministicReportGenerator` provides a completely deterministic reporting implementation.

It generates an executive summary based on the already-established assessment status.

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

The deterministic generator is important for two reasons:

1. it provides a reliable reporting mechanism independent of external services;
2. it establishes a baseline against which LLM-generated reporting can be compared.

---

# 25. LLM Report Generator

`LLMReportGenerator` introduces generative AI exclusively at the reporting stage.

The processing pipeline is:

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
LLMClient
        │
        ▼
Generated Text
        │
        ▼
Response Validation
        │
        ▼
Report
```

The LLM receives structured information that has already been generated by the deterministic system.

The prompt may include:

* assessment status;
* key findings;
* risk factors;
* limitations.

The model therefore acts as a **controlled natural-language generation component**, rather than as a decision engine.

---

# 26. LLM Abstraction

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

This follows the Dependency Inversion Principle.

The reporting layer depends on an interface rather than on a concrete provider.

Consequently, the provider can be replaced without changing:

* `AssessmentService`;
* `RuleEngine`;
* `AnalysisAgent`;
* `ReportingAgent`.

---

# 27. Mock LLM Client

`MockLLMClient` is used for automated testing.

It allows the project to test LLM-dependent components without performing real external API calls.

Advantages include:

* deterministic test behavior;
* fast execution;
* no network dependency;
* no API cost;
* reproducible CI execution.

This is particularly important for maintaining a strict separation between software correctness tests and external model behavior.

---

# 28. Gemini Integration

`GeminiClient` provides the real LLM integration.

The API key is supplied through an environment variable and is not committed to the repository.

Example PowerShell configuration:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

Real integration checks are intentionally kept outside the standard automated test suite.

This prevents CI from depending on:

* external API availability;
* network connectivity;
* API quotas;
* model availability;
* API costs.

---

# 29. LLM Response Validation

LLM output is treated as **untrusted generated content**.

The response is validated before being accepted by the reporting layer.

The validation process verifies, among other things:

1. the response is not empty;
2. the expected deterministic assessment status is preserved;
3. the response satisfies the reporting contract.

The key principle is that the system does **not reconstruct the credit assessment from the generated text**.

Instead:

```text
Deterministic Assessment
        │
        ▼
AssessmentAnalysis
        │
        ├───────────────────────┐
        │                       │
        ▼                       ▼
   Structured Data         LLM Summary
        │                       │
        └───────────┬───────────┘
                    ▼
                  Report
```

The generated executive summary is therefore subordinate to the deterministic domain state.

---

# 30. Failure Handling and Deterministic Fallback

External LLM calls may fail.

Possible failures include:

* network errors;
* API errors;
* authentication failures;
* provider unavailability;
* client exceptions;
* empty responses;
* invalid generated responses;
* failed response validation.

The architecture isolates these failures from the assessment engine.

```text
                 ReportingAgent
                       │
                       ▼
               LLMReportGenerator
                       │
                 LLM success?
                  /          \
                YES           NO
                 │             │
                 ▼             ▼
            LLM Report    Deterministic
                          ReportGenerator
                 │             │
                 └──────┬──────┘
                        ▼
                      Report
```

The fallback consumes the same `AssessmentAnalysis`.

The assessment is therefore never recalculated during fallback.

---

# 31. Workflow

`AssessmentWorkflow` coordinates the complete processing chain.

```text
CreditPosition
      │
      ▼
AssessmentService
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
      ▼
Report
```

The workflow returns an `AssessmentWorkflowResult` containing:

```text
assessment
analysis
report
```

Keeping the three intermediate states explicit makes the workflow observable and independently testable.

---

# 32. Orchestration

`AssessmentOrchestrator` provides the application-level entry point.

Its responsibility is deliberately narrow:

```text
Orchestrator
      │
      ▼
Workflow.run(position)
      │
      ▼
Report
```

The orchestrator does not implement credit logic.

It delegates execution to the workflow.

This is explicitly tested through dependency mocking to guarantee that the orchestrator remains a thin coordination layer.

---

# 33. Factories and Dependency Injection

The project uses factories to construct the default application configuration.

Examples include:

```text
create_default_assessment_service()
create_default_orchestrator()
```

Factories assemble the required dependencies:

```text
RuleEngine
CommentEngine
AssessmentStatusCalculator
AssessmentService
AnalysisAgent
ReportingAgent
Workflow
Orchestrator
```

This keeps application composition separate from domain logic.

It also makes testing easier because individual components can be constructed with mocks or alternative implementations.

---

# 34. Project Structure

The current source structure is organized according to architectural responsibility.

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
│   ├── report.py
│   └── rule_finding.py
│
├── orchestration/
│   ├── orchestrator.py
│   └── orchestrator_factory.py
│
├── rules/
│   ├── base/
│   │   ├── config.py
│   │   ├── rule.py
│   │   ├── severity.py
│   │   ├── severity_direction.py
│   │   ├── severity_policy.py
│   │   ├── severity_threshold.py
│   │   └── status.py
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
├── engine/
├── integration/
├── models/
├── rules/
├── services/
└── conftest.py

config/
└── rules.yaml

scripts/
└── check_gemini_workflow.py
```

The exact number of rule and test modules may evolve as the project grows.

---

# 35. Testing Strategy

Testing is organized around the architecture rather than around implementation details alone.

```text
                    TESTING PYRAMID

                         ▲
                         │
                Real LLM Validation
                         │
                  Integration Tests
                         │
                    Unit Tests
                         │
              Deterministic Components
                         │
                         ▼
```

The deterministic components receive the highest level of automated coverage because they contain the authoritative business logic.

---

# 36. Unit Testing

Unit tests cover individual components in isolation.

Current test coverage includes areas such as:

### Domain Models

* `CreditPosition`;
* `Report`;
* `AssessmentStatus`;
* other domain objects.

Tests verify:

* correct construction;
* field preservation;
* optional values;
* immutability where required.

---

### Rule Infrastructure

Tests cover:

* `RuleConfig`;
* severity levels;
* severity directions;
* severity thresholds;
* `SeverityPolicy`;
* `Rule`;
* `RuleResult`.

The tests explicitly verify boundary behavior.

For example:

```text
threshold = 5.0

5.0 → HIGH
5.1 → HIGH
4.9 → MEDIUM
```

---

### Rule Discovery

Tests verify that:

```python
discover_rules()
```

loads all expected registered rules:

```text
R001
R002
R003
R004
R005
R006
R007
```

They also verify that discovery is idempotent.

---

### Rule Registry

Tests verify:

* unknown rule IDs are rejected;
* default rules are available;
* rule IDs are unique;
* separate calls produce independent rule instances;
* configuration order is preserved;
* configuration objects are preserved;
* configuration thresholds are respected.

---

### Configuration Loading

Tests validate that the YAML configuration is loaded correctly.

They verify:

* rule thresholds;
* default severity;
* severity direction;
* severity thresholds.

This provides an automated consistency check between:

```text
config/rules.yaml
        │
        ▼
RuleConfigLoader
        │
        ▼
RuleConfig
```

---

### Assessment Service

Tests verify:

* critical assessments;
* attention assessments;
* normal assessments;
* non-evaluable rules;
* rule-result preservation;
* finding generation;
* missing comments;
* dependency delegation.

---

### Assessment Status Calculator

Tests explicitly verify the aggregation logic:

```text
0 triggered rules
        → NORMAL

1 triggered rule
        → ATTENTION

2+ triggered rules
        → CRITICAL
```

and confirm that:

```text
NOT_EVALUABLE
```

does not count as a triggered rule.

---

### Orchestration

Tests verify that:

* the orchestrator returns a `Report`;
* assessment status is preserved;
* execution is delegated to the workflow;
* the default orchestrator is correctly constructed;
* findings are preserved.

---

# 37. Integration Testing

Integration tests verify the interaction between multiple components.

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
AssessmentWorkflow
      +
AnalysisAgent
      +
ReportingAgent
```

The goal is to verify that the contracts between architectural layers are respected.

---

# 38. End-to-End Testing

End-to-end scenarios execute the complete deterministic workflow.

A representative scenario is:

```text
CreditPosition
      ↓
Default Assessment Service
      ↓
Rule Evaluation
      ↓
Assessment
      ↓
Analysis
      ↓
Reporting
      ↓
Report
```

The tests verify that the expected information survives the entire pipeline.

For example:

```text
configured rules
        ↓
RuleResult[]
        ↓
triggered rules
        ↓
RuleFinding[]
        ↓
Assessment
        ↓
Report
```

---

# 39. Test Fixtures and `conftest.py`

Shared test dependencies are defined in:

```text
tests/conftest.py
```

For example:

```python
@pytest.fixture
def assessment_service() -> AssessmentService:
    return AssessmentService(
        rule_engine=RuleEngine(get_default_rules()),
        comment_engine=CommentEngine(),
        status_calculator=AssessmentStatusCalculator(),
    )
```

This fixture provides a reusable default assessment service to tests that need the standard deterministic configuration.

The purpose of `conftest.py` is not to define an additional test.

It is a **pytest configuration and fixture module** automatically discovered by pytest.

Therefore:

```text
tests/conftest.py
```

is infrastructure for the test suite rather than a test case itself.

---

# 40. Mocking Strategy

Mocks are used where a test should isolate a component from its dependencies.

For example, `AssessmentService` can be tested using mocked:

```text
RuleEngine
CommentEngine
AssessmentStatusCalculator
```

This allows the test to verify orchestration behavior without re-testing the implementation of every dependency.

Similarly, the orchestrator is tested with a mocked workflow:

```text
AssessmentOrchestrator
        │
        ▼
Mock(AssessmentWorkflow)
```

The test then verifies:

```python
workflow.run.assert_called_once_with(position)
```

This explicitly enforces the intended dependency boundary.

---

# 41. LLM Testing Strategy

Automated tests do not depend on a real external LLM.

Instead:

```text
LLMClient
    │
    └── MockLLMClient
```

is used for deterministic testing.

Tests can therefore validate:

* valid responses;
* empty responses;
* invalid responses;
* missing status;
* client exceptions;
* fallback behavior;
* preservation of deterministic findings;
* preservation of limitations.

Real Gemini execution is reserved for dedicated integration checks.

---

# 42. Real LLM Validation

Real Gemini calls are intentionally separated from the automated test suite.

The manual validation script is:

```powershell
python -m scripts.check_gemini_workflow
```

The real integration workflow validates representative scenarios such as:

```text
NORMAL
ATTENTION
CRITICAL
```

The objective is to verify the behavior of the complete system with an actual LLM without making the CI pipeline dependent on an external service.

Real LLM validation focuses on:

* consistency with deterministic assessment status;
* reporting quality;
* preservation of findings;
* preservation of risk factors;
* preservation of limitations;
* robustness of response validation;
* fallback behavior.

---

# 43. Static Analysis

Ruff is used for linting and static code analysis.

Run:

```powershell
python -m ruff check .
```

Ruff checks the repository for issues such as:

* unused imports;
* undefined names;
* invalid code patterns;
* style violations covered by the configured rules.

The goal is to keep the codebase clean and consistent before changes are merged.

---

# 44. Automated Test Execution

Run the complete test suite with:

```powershell
python -m pytest
```

For coverage:

```powershell
python -m pytest --cov=src --cov-report=term-missing
```

The exact number of tests is intentionally not hard-coded in this README because the test suite is expected to evolve with the project.

The relevant quality criterion is that the complete test suite passes.

---

# 45. Continuous Integration

The project uses GitHub Actions to automate software quality checks.

The CI pipeline is designed to verify that changes do not introduce regressions in the deterministic assessment system or its supporting architecture.

Typical checks include:

```text
Code checkout
      ↓
Python environment
      ↓
Dependency installation
      ↓
Ruff
      ↓
Pytest
      ↓
Coverage / quality checks
```

Real external LLM calls are deliberately excluded from the standard CI pipeline.

This preserves deterministic and reproducible builds.

---

# 46. Quality Gates

A change should be considered valid only when the relevant quality gates are satisfied:

```text
✓ Tests pass
✓ Ruff passes
✓ Architectural contracts remain valid
✓ Deterministic assessment behavior is preserved
✓ LLM boundary is preserved
✓ No secrets are committed
```

In particular, changes to rules should be accompanied by corresponding tests and, where applicable, configuration updates.

---

# 47. Development Workflow

A typical development cycle is:

```text
1. Modify implementation
        ↓
2. Update/add tests
        ↓
3. Run pytest
        ↓
4. Run Ruff
        ↓
5. Review architectural impact
        ↓
6. Commit
        ↓
7. Push
        ↓
8. GitHub Actions
```

For rule changes, the recommended sequence is:

```text
Rule implementation
        ↓
Rule configuration
        ↓
Rule tests
        ↓
Registry/discovery tests
        ↓
Assessment service tests
        ↓
Integration tests
```

This helps prevent changes from silently propagating into unrelated parts of the system.

---

# 48. Adding a New Rule

Adding a new rule generally requires changes across several layers.

A typical process is:

```text
1. Define the rule
        ↓
2. Add configuration
        ↓
3. Register/discover the rule
        ↓
4. Add rule-specific tests
        ↓
5. Update configuration tests
        ↓
6. Update integration scenarios
        ↓
7. Run pytest + Ruff
```

For example, introducing `R008` may require:

```text
src/rules/...
config/rules.yaml
tests/rules/...
tests/integration/...
```

The registry architecture ensures that the rule can then participate in the same deterministic workflow as the existing rules.

---

# 49. Configuration as a Business Boundary

One of the important design choices is the separation between **business parameters** and **business logic**.

Instead of hard-coding:

```python
if value < -0.10:
```

the architecture can represent the business parameter through configuration:

```text
RuleConfig
    threshold = -0.10
```

This creates a cleaner boundary:

```text
Business Policy
      │
      ▼
Configuration
      │
      ▼
Rule Implementation
```

It also improves auditability because threshold changes can be identified independently from code changes.

---

# 50. Auditability and Explainability

The deterministic architecture is designed to support traceability.

A final assessment can be traced back through:

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
RuleConfig
```

This creates an explicit chain between:

```text
Final assessment
        ↓
Triggered rule
        ↓
Observed value
        ↓
Threshold
        ↓
Severity
```

This traceability is particularly relevant for credit-risk applications, where explainability and reproducibility are important requirements.

---

# 51. Why the LLM Is Not the Decision Engine

Using an LLM directly for credit assessment would introduce several undesirable properties:

```text
Probabilistic output
        +
Non-deterministic reasoning
        +
Potential hallucination
        +
Weak reproducibility
        +
Difficulty auditing thresholds
```

The proposed architecture instead uses:

```text
Deterministic rules
        +
Explicit configuration
        +
Structured results
        +
Controlled LLM reporting
```

The LLM is therefore used where generative models provide the greatest value:

> **Natural-language synthesis and communication of already-established analytical results.**

---

# 52. Current Scope

The current prototype focuses on demonstrating:

* deterministic credit assessment;
* configurable financial rules;
* explicit severity policies;
* rule discovery and registry;
* structured domain models;
* assessment aggregation;
* rule findings and comments;
* multi-agent workflow;
* deterministic reporting;
* LLM-assisted reporting;
* provider-independent LLM integration;
* response validation;
* deterministic fallback;
* automated testing;
* static analysis;
* continuous integration.

The project currently does not require:

* relational databases;
* NoSQL databases;
* REST APIs;
* message queues;
* microservices;
* Kubernetes;
* Terraform;
* vector databases;
* retrieval-augmented generation.

These technologies can be introduced later if justified by deployment or functional requirements.

---

# 53. Security and Data Handling

The prototype is designed so that sensitive credit information can be kept outside the repository and externalized from the codebase.

Recommended practices include:

* use anonymized or synthetic test positions;
* never commit API keys;
* store credentials in environment variables or secret managers;
* avoid sending unnecessary sensitive information to external LLM providers;
* maintain deterministic assessment logic independently from external services.

For real-world deployment, additional controls would be required around:

* data minimization;
* encryption;
* access control;
* audit logging;
* provider-specific data-retention policies;
* regulatory requirements;
* model governance.

---

# 54. Current Implementation Status

The current implementation provides:

```text
✓ Structured CreditPosition domain model
✓ Deterministic rule-based assessment
✓ RuleConfig abstraction
✓ YAML rule configuration
✓ SeverityDirection
✓ SeverityThreshold
✓ SeverityPolicy
✓ Explicit RuleStatus
✓ Explicit RuleSeverity
✓ Immutable RuleConfig
✓ Immutable RuleResult
✓ Rule discovery
✓ Rule registry
✓ Independent rule instances
✓ Configurable rule thresholds
✓ Seven registered rules
✓ AssessmentStatusCalculator
✓ AssessmentService
✓ RuleFinding / CommentEngine
✓ Analysis Agent
✓ Reporting Agent
✓ Deterministic report generation
✓ LLM report generation
✓ Provider-independent LLM abstraction
✓ Mock LLM client
✓ Gemini client
✓ LLM response validation
✓ Deterministic fallback
✓ Assessment workflow
✓ Application-level orchestrator
✓ Dependency injection
✓ Factory-based composition
✓ Unit tests
✓ Integration tests
✓ End-to-end tests
✓ Shared pytest fixtures
✓ Ruff static analysis
✓ GitHub Actions CI
✓ Real Gemini integration checks
```

---

# 55. Documentation Structure

The repository documentation is organized according to the project's principal concerns.

| Document               | Purpose                                                           |
| ---------------------- | ----------------------------------------------------------------- |
| `README.md`            | Project overview, architecture, usage, testing and current status |
| `docs/architecture.md` | Detailed architectural design and design rationale                |
| `docs/validation.md`   | Validation methodology, scenarios, test levels and limitations    |

The README provides the global picture.

The architecture document can then explain design decisions in greater technical depth, while the validation document can focus specifically on how the system is evaluated.

---

# 56. Future Development

Potential extensions include:

### Assessment Engine

* additional financial indicators;
* additional credit-risk rules;
* richer rule dependencies;
* historical trend analysis;
* configurable rule weighting;
* more sophisticated status aggregation.

### Analysis Layer

* richer risk-factor classification;
* cross-rule analytical relationships;
* structured recommendations;
* temporal analysis;
* portfolio-level aggregation.

### LLM Layer

* additional LLM providers;
* local LLM support;
* structured JSON responses;
* stronger schema validation;
* automated faithfulness evaluation;
* hallucination detection;
* prompt versioning;
* model comparison;
* latency and cost monitoring.

### Application Layer

* REST API;
* Streamlit demonstration interface;
* web frontend;
* database persistence;
* authentication and authorization;
* audit logging.

### Engineering

* Docker;
* infrastructure as code;
* deployment automation;
* expanded CI/CD;
* performance testing;
* security testing.

All future extensions should preserve the central architectural boundary:

```text
Deterministic assessment
            │
            ▼
      Structured analysis
            │
            ▼
      Optional generation
```

---

# 57. Architectural Summary

The complete architecture can be summarized as:

```text
                         CREDIT POSITION
                               │
                               ▼
                     ┌───────────────────┐
                     │ AssessmentService │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │    RuleEngine     │
                     └─────────┬─────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
           R001              R002              R00N
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                        RuleResult[]
                               │
                               ▼
                  AssessmentStatusCalculator
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
                ┌──────────────┴──────────────┐
                ▼                             ▼
       Deterministic Generator          LLM Generator
                                              │
                                              ▼
                                          LLMClient
                                              │
                                   ┌──────────┴──────────┐
                                   ▼                     ▼
                                 Gemini                 Mock
                                   │
                                   └──────────┬──────────┘
                                              ▼
                                            Report
```

The critical boundary is:

```text
                 SOURCE OF TRUTH
                       │
                       ▼
              DETERMINISTIC LAYER
                       │
          ┌────────────┴────────────┐
          │                         │
     Rule Results              Assessment
          │                         │
          └────────────┬────────────┘
                       ▼
                Structured Analysis
                       │
                       ▼
              OPTIONAL LLM LAYER
                       │
                       ▼
                 Natural Language
```

The LLM can improve how the assessment is communicated, but it cannot redefine what the assessment is.

---

# 58. Final Design Principle

The fundamental design principle of the `credit-assessment-system` is:

> **The deterministic layer decides; the agent layer structures; the LLM communicates.**

This separation provides a practical compromise between traditional rule-based credit assessment and generative AI.

The resulting architecture is:

```text
Deterministic
      +
Configurable
      +
Traceable
      +
Testable
      +
Modular
      +
LLM-assisted
```

while explicitly avoiding:

```text
LLM-driven credit decisions
```

The deterministic assessment engine therefore remains the **source of truth**, while the analysis and reporting layers provide increasingly sophisticated mechanisms for structuring and communicating the result.
