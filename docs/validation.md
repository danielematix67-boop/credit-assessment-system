# System Validation

## 1. Validation Scope and Objectives

The validation of the `credit-assessment-system` is designed to verify that the implemented system satisfies its functional, architectural, and reliability requirements.

The validation focuses on four primary dimensions:

1. **Functional correctness** — individual components and complete workflows produce the expected results.
2. **Assessment integrity** — the deterministic assessment remains authoritative throughout the entire processing pipeline.
3. **LLM integration safety** — the LLM is restricted to the reporting layer and cannot modify the structured assessment.
4. **Operational resilience** — failures in the external LLM service do not invalidate the deterministic assessment or prevent report generation when a fallback generator is available.

The validation is therefore not intended to evaluate the predictive performance of a statistical or machine-learning model. Instead, it evaluates the correctness, consistency, traceability, and architectural integrity of a rule-based credit assessment system augmented with generative AI.

The central validation principle is:

> **The deterministic assessment must remain correct and authoritative regardless of the behavior or availability of the LLM.**

This principle is reflected throughout the testing strategy and represents the primary architectural invariant of the system.

---

# 2. Verification and Validation Strategy

The project adopts a multi-level testing and validation strategy.

```text
                    SYSTEM VALIDATION
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     Unit Testing    Integration Testing   Scenario
                                           Validation
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                 End-to-End Validation
                           │
                           ▼
                 External LLM Validation
```

Each validation level addresses a different category of risk.

The strategy combines automated software testing with scenario-based validation in order to verify both implementation correctness and architectural behavior.

---

## 2.1 Unit Testing

Unit tests verify individual components in isolation and ensure that their interfaces and behavioral contracts are respected.

The main components subject to unit testing include:

* domain models;
* assessment rules;
* rule configuration;
* severity configuration;
* rule discovery;
* rule registration;
* rule engine;
* assessment service;
* assessment status calculation;
* analysis agent;
* assessment analysis;
* reporting components;
* deterministic report generation;
* LLM report generation;
* LLM response validation;
* LLM client abstractions;
* mock LLM client;
* workflow components;
* orchestration components.

Unit testing is particularly important for the deterministic assessment layer because each individual rule must produce reproducible results for the same input and configuration.

A deterministic rule should therefore satisfy the following property:

```text
Same Input
    +
Same Configuration
    ↓
Same Rule Result
```

---

## 2.2 Integration Testing

Integration tests verify that independently implemented components operate correctly when combined.

The principal integration chain is:

```text
Rule Engine
     ↓
Assessment Service
     ↓
Analysis Agent
     ↓
Reporting Agent
     ↓
Report Generator
```

Integration tests verify, among other aspects:

* propagation of deterministic rule results;
* generation of deterministic findings;
* propagation of the assessment status;
* transformation from `Assessment` to `AssessmentAnalysis`;
* preservation of risk factors;
* preservation of limitations;
* transformation from `AssessmentAnalysis` to `Report`;
* selection of the configured report generator;
* LLM reporting behavior;
* deterministic fallback behavior.

Integration testing is particularly important because many architectural guarantees depend on the correct interaction between components rather than on the behavior of an individual class.

---

## 2.3 End-to-End Testing

End-to-end tests execute the complete application workflow starting from a `CreditPosition` and ending with a `Report`.

The complete processing chain is:

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
ReportGenerator
      │
      ▼
Report
```

End-to-end validation verifies that information is correctly propagated through every stage.

In particular, the following invariant must hold:

```text
Assessment
     │
     ├── status ────────────────┐
     │                          │
     ▼                          ▼
AssessmentAnalysis.status   Report.assessment_status
```

The final report must therefore remain consistent with the deterministic assessment that originated the workflow.

---

# 3. Deterministic Assessment Validation

The deterministic assessment layer represents the authoritative decision-making component of the system.

Its responsibility is to transform structured financial information into a reproducible assessment.

The core flow is:

```text
Financial Data
      │
      ▼
Assessment Rules
      │
      ▼
Rule Results
      │
      ▼
Assessment
```

The assessment layer is responsible for:

* evaluating financial indicators;
* applying configured business rules;
* determining rule severity;
* generating structured findings;
* calculating the overall assessment status.

The LLM is not involved in any of these activities.

---

## 3.1 Deterministic Rule Evaluation

Each rule evaluates a specific financial condition or relationship.

Examples include rules related to:

```text
Revenue Growth
EBITDA
Profitability
EBITDA Margin
PFN-to-EBITDA
Financial Expenses
Interest Coverage
Other Financial Indicators
```

Each rule produces a structured `RuleResult`.

Conceptually:

```text
Financial Indicator
        │
        ▼
Business Rule
        │
        ▼
RuleResult
```

The validation verifies that:

* the correct rule is executed;
* the correct input indicator is used;
* thresholds are applied correctly;
* severity is determined according to configuration;
* `NOT_EVALUABLE` conditions are handled correctly;
* the resulting `RuleResult` is structurally valid.

The expected property is:

```text
Same Input
    +
Same Rule Configuration
    ↓
Same Rule Result
```

---

# 4. Rule Configuration Validation

Rule behavior is partly controlled through explicit configuration.

The validation therefore distinguishes between:

```text
Rule Logic
```

and:

```text
Rule Configuration
```

The configuration may include:

* rule identifier;
* rule name;
* category;
* primary threshold;
* default severity;
* severity direction;
* severity thresholds.

Validation verifies that the configured parameters are correctly interpreted by the rule implementation.

Conceptually:

```text
Rule
 │
 ├── Rule Configuration
 │       ├── Threshold
 │       ├── Severity
 │       ├── Severity Direction
 │       └── Severity Thresholds
 │
 └── Evaluation
```

This separation is important because business-policy changes should not require modifications to unrelated application components.

---

# 5. Assessment Status Validation

The system supports a deterministic overall assessment status.

The principal states are:

```text
NORMAL
ATTENTION
CRITICAL
```

The status is calculated exclusively from deterministic assessment results.

The LLM has no role in this calculation.

The intended dependency is:

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

Validation therefore verifies that:

* identical inputs produce identical assessment statuses;
* status calculation is independent of the LLM;
* changes in LLM output do not alter the deterministic status;
* changes in LLM availability do not alter the deterministic status.

The central invariant is:

```text
Assessment.status
```

is determined entirely by:

```text
Deterministic Assessment Results
+
Configured Assessment Logic
```

---

# 6. Assessment Integrity

A fundamental validation requirement is that the deterministic assessment remains unchanged throughout the workflow.

The assessment status is propagated through the different processing stages:

```text
Assessment.status
       │
       ▼
AssessmentAnalysis.assessment_status
       │
       ▼
Report.assessment_status
```

The validation verifies the following invariant:

```text
Assessment.status
    =
AssessmentAnalysis.assessment_status
    =
Report.assessment_status
```

The same principle applies to deterministic findings.

The findings generated by the assessment layer must remain the authoritative structured findings exposed by the analysis and reporting layers.

Conceptually:

```text
Deterministic Findings
        │
        ▼
Analysis Findings
        │
        ▼
Report Findings
```

The LLM must not be able to replace or redefine these findings.

---

# 7. Finding Integrity

Findings originate from deterministic rule evaluations.

The conceptual chain is:

```text
Rule
  ↓
RuleResult
  ↓
Finding
  ↓
Assessment
  ↓
AssessmentAnalysis
  ↓
Report
```

Validation verifies that the relationship between a finding and its originating rule is preserved throughout the workflow.

For each deterministic finding, the system should preserve information such as:

* originating rule;
* category;
* evaluated value;
* severity;
* associated comment or explanation.

The report generation layer therefore does not need to independently rediscover why a finding exists.

This provides traceability from the final report back to the underlying deterministic rule evaluation.

---

# 8. Non-Evaluable Conditions

The system must distinguish between a rule that does not trigger and a rule that cannot be evaluated.

A rule may therefore return:

```text
NOT_EVALUABLE
```

rather than:

```text
TRIGGERED
```

or:

```text
NOT_TRIGGERED
```

Validation verifies that non-evaluable conditions are handled explicitly.

The expected behavior is:

```text
Rule Result = NOT_EVALUABLE
             │
             ▼
        No Finding
```

A missing or unsuitable input should not automatically be interpreted as a negative credit signal.

Validation therefore checks that:

* `NOT_EVALUABLE` results are represented correctly;
* non-evaluable rules do not incorrectly create findings;
* non-evaluable rules do not incorrectly alter the assessment status;
* the analysis does not incorrectly expose them as negative findings;
* the final report does not present them as deterministic risk findings.

---

# 9. Analysis Layer Validation

The `AnalysisAgent` transforms the deterministic `Assessment` into an `AssessmentAnalysis`.

It does not perform a second credit assessment.

The expected transformation is:

```text
Assessment
    │
    ▼
AnalysisAgent
    │
    ▼
AssessmentAnalysis
```

Validation verifies that the analysis layer:

* preserves the assessment status;
* preserves deterministic findings;
* identifies relevant risk factors;
* preserves limitations;
* does not introduce unsupported assessment outcomes;
* does not override deterministic information.

The analysis layer therefore acts as a controlled intermediate representation between assessment and reporting.

---

# 10. Assessment Analysis Integrity

`AssessmentAnalysis` represents the structured information made available to the reporting layer.

Its main elements include:

```text
AssessmentAnalysis
│
├── Assessment Status
├── Key Findings
├── Risk Factors
└── Limitations
```

Validation verifies that these elements remain consistent with the originating deterministic assessment.

In particular:

```text
Assessment.status
        ↓
AssessmentAnalysis.assessment_status
```

must be a direct propagation of the deterministic status rather than a newly inferred value.

Similarly:

```text
Assessment findings
        ↓
AssessmentAnalysis findings
```

must preserve the deterministic findings.

This prevents the analysis agent from becoming an alternative decision engine.

---

# 11. LLM Reporting Validation

The LLM is deliberately isolated within the reporting layer.

Its purpose is to generate a natural-language executive summary from an already structured `AssessmentAnalysis`.

The LLM receives controlled information such as:

* assessment status;
* key findings;
* risk factors;
* limitations.

The LLM is explicitly instructed not to:

* introduce unsupported financial information;
* invent causes or trends;
* modify the assessment status;
* make an independent credit decision;
* modify deterministic findings;
* remove deterministic findings;
* modify limitations;
* introduce unsupported recommendations;
* infer missing information;
* disclose internal rule thresholds.

The generated response is treated as **untrusted external content**.

It is therefore validated before being accepted as the executive summary of the final report.

---

# 12. LLM Response Validation

The current validation mechanism performs basic consistency checks on generated output.

The validation flow is:

```text
LLM Response
      │
      ▼
Response Validation
      │
      ├── Invalid ──────► Fallback
      │
      └── Valid
             │
             ▼
          Report
```

At minimum, the validation verifies that the response is usable and consistent with the deterministic assessment.

---

## 12.1 Non-Empty Response

An empty or whitespace-only response is rejected.

```text
LLM Response
     │
     ▼
Empty?
     │
   YES
     │
     ▼
Validation Failure
     │
     ▼
Fallback
```

This prevents an unsuccessful model invocation from being interpreted as a valid executive summary.

---

## 12.2 Assessment Status Preservation

The generated response must remain consistent with the deterministic assessment status.

For example, if:

```text
Assessment status = CRITICAL
```

the generated response must not communicate a contradictory classification.

The current validation therefore checks for the expected deterministic status in the generated response.

If the expected status is absent, the response is rejected and the fallback mechanism is activated.

This provides a basic consistency check between:

```text
Structured Assessment
```

and:

```text
Generated Narrative
```

---

# 13. LLM Cannot Replace Deterministic Findings

The structured findings contained in the final report are not generated by the LLM.

They originate from the deterministic assessment pipeline:

```text
Rule
  ↓
RuleResult
  ↓
Finding
  ↓
Assessment
  ↓
AssessmentAnalysis
  ↓
Report
```

The LLM is responsible only for the executive summary.

This architectural property is validated by ensuring that generated narrative content does not become part of the structured finding collection.

For example, if an LLM produces an unsupported statement that does not correspond to any deterministic finding, that statement must remain confined to the generated narrative and must not modify the structured assessment.

The fundamental relationship is therefore:

```text
LLM-generated narrative
        ≠
Deterministic findings
```

The latter remain authoritative.

---

# 14. LLM Cannot Replace Deterministic Limitations

The same principle applies to limitations.

Limitations are produced and controlled by the deterministic application logic and propagated through the reporting pipeline.

The expected relationship is:

```text
AssessmentAnalysis.limitations
          =
Report.limitations
```

The LLM cannot replace, remove, or redefine these structured limitations.

This is particularly important when a credit position cannot be fully evaluated because certain financial information is unavailable.

The final report must preserve this limitation independently of the generated narrative.

---

# 15. Reporting Layer Validation

The reporting layer supports two report-generation strategies:

```text
ReportGenerator
      │
      ├── LLMReportGenerator
      │
      └── DeterministicReportGenerator
```

Validation verifies that both generators operate against the same `AssessmentAnalysis`.

This ensures that the choice of reporting strategy does not change the underlying assessment.

The expected property is:

```text
Same AssessmentAnalysis
        │
        ├── DeterministicReportGenerator
        │
        └── LLMReportGenerator
```

with:

```text
Same Assessment Status
Same Structured Findings
Same Limitations
```

while the natural-language executive summary may differ.

This is a key validation property because it demonstrates that reporting technology does not alter the underlying assessment.

---

# 16. Deterministic Report Generator Validation

The `DeterministicReportGenerator` provides a reporting path that does not depend on an external LLM.

Validation verifies that it:

* produces a valid report;
* preserves the assessment status;
* preserves structured findings;
* preserves limitations;
* operates without network connectivity;
* can be executed deterministically;
* can act as a fallback when LLM generation fails.

The expected behavior is:

```text
AssessmentAnalysis
        │
        ▼
DeterministicReportGenerator
        │
        ▼
      Report
```

This generator provides the baseline against which the LLM-based reporting path can be compared.

---

# 17. LLM Report Generator Validation

`LLMReportGenerator` is validated separately from the deterministic assessment logic.

Validation verifies that the generator:

* receives the expected `AssessmentAnalysis`;
* constructs a controlled prompt;
* communicates through the `LLMClient` abstraction;
* handles the generated response;
* validates the response;
* constructs the final report without modifying structured deterministic information.

The LLM is therefore treated as a reporting dependency rather than as a component of the assessment engine.

---

# 18. LLM Client Abstraction Validation

The reporting layer depends on the `LLMClient` abstraction rather than directly on a specific provider.

The architecture is:

```text
LLMReportGenerator
        │
        ▼
     LLMClient
        │
        ├── GeminiClient
        ├── MockLLMClient
        └── Future Provider
```

Validation verifies that:

* `LLMReportGenerator` can operate against the abstraction;
* the mock implementation can replace the external provider;
* provider-specific behavior remains isolated;
* changing the provider does not require changes to the assessment layer.

This verifies the intended dependency-inversion boundary.

---

# 19. Mock LLM Validation

`MockLLMClient` provides deterministic LLM behavior for automated testing.

It avoids dependencies on:

* network connectivity;
* external API availability;
* API quotas;
* API costs;
* model stochasticity.

The mock can also expose the generated prompt, allowing tests to verify prompt construction where required.

The expected testing architecture is:

```text
Automated Tests
      │
      ▼
MockLLMClient
      │
      ▼
Deterministic Test Behaviour
```

This ensures that automated tests remain reproducible and independent from external generative services.

---

# 20. External LLM Validation

The concrete LLM provider integration is validated separately from the automated deterministic test suite.

The external integration should be evaluated for:

* successful request execution;
* authentication;
* provider errors;
* unavailable services;
* quota-related failures;
* timeout behavior;
* malformed or unexpected responses;
* response validation.

External integration tests should not be required for every execution of the automated test suite.

This separation ensures that:

```text
Software Correctness
        ≠
External Service Availability
```

---

# 21. LLM Failure Handling and Deterministic Fallback

External LLM services introduce operational dependencies that do not exist in the deterministic assessment layer.

Potential failures include:

* service unavailability;
* authentication errors;
* permission errors;
* quota exhaustion;
* request timeouts;
* unexpected API failures;
* invalid generated responses.

The system therefore implements a fallback mechanism in the `ReportingAgent`.

The intended architecture is:

```text
                     ReportingAgent
                           │
                           ▼
                 LLMReportGenerator
                           │
                  ┌────────┴────────┐
                  │                 │
               Success            Failure
                  │                 │
                  ▼                 ▼
              LLM Report    DeterministicReportGenerator
                  │                 │
                  └────────┬────────┘
                           ▼
                         Report
```

When the LLM fails:

1. the deterministic assessment remains unchanged;
2. the assessment analysis remains unchanged;
3. the reporting failure is recorded;
4. the fallback generator is invoked;
5. a deterministic report is produced.

This establishes the resilience property:

> **Failure of the generative reporting component must not cause failure of the deterministic credit assessment.**

---

# 22. Fallback Validation

The fallback mechanism is explicitly validated using controlled failure conditions.

A failing LLM client can be used to simulate external service problems.

Validation verifies that:

* the deterministic assessment remains valid;
* the assessment status remains unchanged;
* the analysis remains unchanged;
* the fallback generator is selected;
* a valid report is produced;
* structured findings remain unchanged;
* limitations remain unchanged.

The reporting agent also exposes runtime diagnostics such as:

```text
last_generator_used
last_error
```

These values provide basic observability of the reporting path.

For example:

```text
last_generator_used = PRIMARY
```

indicates that the primary report generator was successfully used.

Whereas:

```text
last_generator_used = FALLBACK
```

indicates that fallback reporting was activated.

---

# 23. Fallback Independence from Assessment

An important validation property is that fallback execution must not rerun or modify the deterministic assessment.

The intended flow is:

```text
Assessment
    │
    ▼
AssessmentAnalysis
    │
    ▼
LLM Reporting
    │
    ├── Success ───────► Report
    │
    └── Failure
            │
            ▼
    Deterministic Reporting
            │
            ▼
          Report
```

The fallback operates on the existing `AssessmentAnalysis`.

It does not:

* recalculate rules;
* modify findings;
* modify severity;
* recalculate assessment status;
* reinterpret limitations.

This ensures that fallback reporting remains a presentation concern rather than becoming a second assessment path.

---

# 24. Workflow Validation

`AssessmentWorkflow` coordinates the three primary stages:

```text
1. Assessment
2. Analysis
3. Reporting
```

The expected execution is:

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

Validation verifies that:

* each stage is executed in the correct order;
* outputs are correctly passed to the next stage;
* deterministic information is preserved;
* reporting failures do not invalidate previous stages;
* the final `AssessmentWorkflowResult` contains the expected assessment, analysis, and report.

This ensures that orchestration remains separate from business-rule implementation.

---

# 25. Orchestrator Validation

The `Orchestrator` provides the application-level entry point for executing the complete workflow.

Validation verifies that the orchestrator:

* correctly constructs or receives the workflow dependencies;
* invokes the assessment workflow;
* returns the expected workflow result;
* does not introduce additional assessment logic;
* does not bypass the deterministic assessment layer.

The intended architecture is:

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

The orchestrator therefore coordinates execution rather than implementing domain decisions.

---

# 26. Factory Validation

Factory functions centralize dependency construction and default configuration.

Examples include:

```text
create_default_assessment_workflow()
create_default_orchestrator()
```

Validation verifies that factories construct compatible components and preserve the intended dependency graph.

For example:

```text
Factory
  │
  ├── AssessmentService
  ├── AnalysisAgent
  ├── ReportingAgent
  ├── LLMReportGenerator
  └── DeterministicReportGenerator
```

Factory validation is important because incorrect dependency wiring could invalidate the intended architecture even if individual components are correct in isolation.

---

# 27. Scenario-Based Validation

In addition to automated testing, the system should be evaluated using representative credit-assessment scenarios.

The scenarios are designed to exercise the principal assessment states:

```text
NORMAL
ATTENTION
CRITICAL
```

Each scenario is processed through the complete workflow.

The validation examines:

* deterministic assessment status;
* triggered findings;
* risk factors;
* limitations;
* generated executive summary;
* consistency between structured and generated information;
* behavior of the fallback mechanism where applicable.

Scenario-based validation complements automated unit and integration testing by evaluating the behavior of the complete system under representative business conditions.

---

## 27.1 NORMAL Scenario

The `NORMAL` scenario represents a position whose financial indicators remain within the configured acceptable ranges.

Expected result:

```text
Assessment Status = NORMAL
```

The report should communicate the normal assessment without introducing unsupported risk factors.

The structured report content must remain consistent with the deterministic assessment.

---

## 27.2 ATTENTION Scenario

The `ATTENTION` scenario represents a position where one or more indicators require monitoring but the deterministic rules do not classify the overall position as critical.

Expected result:

```text
Assessment Status = ATTENTION
```

The generated report should accurately communicate the areas requiring attention while preserving the deterministic assessment status.

---

## 27.3 CRITICAL Scenario

The `CRITICAL` scenario represents a position affected by significant adverse indicators.

Expected result:

```text
Assessment Status = CRITICAL
```

The report should communicate the critical status and summarize the relevant deterministic findings.

The LLM must not introduce an alternative assessment classification.

---

# 28. Adversarial LLM Validation

Because LLM output is inherently less deterministic than rule evaluation, validation should also consider deliberately problematic responses.

Examples include an LLM response that:

* states a different assessment status;
* introduces an unsupported financial metric;
* invents a causal explanation;
* introduces a finding that does not exist;
* removes a deterministic finding from the narrative;
* claims that missing information is known;
* introduces an unsupported recommendation;
* returns an empty response;
* returns malformed content.

The purpose of these tests is not to prove that the LLM can never produce incorrect content.

Instead, the objective is to verify that incorrect generative behavior cannot modify the authoritative structured assessment.

The conceptual validation is:

```text
Adversarial LLM Output
          │
          ▼
      Validation
          │
     ┌────┴────┐
     │         │
  Accepted   Rejected
     │         │
     ▼         ▼
 Report      Fallback
```

This approach treats the LLM as an untrusted component whose output must remain within the boundaries established by the application.

---

# 29. Deterministic–Generative Consistency

A central validation objective is to ensure consistency between deterministic information and generated narrative.

The system maintains two distinct information categories:

```text
AUTHORITATIVE INFORMATION
        │
        ├── Assessment Status
        ├── Structured Findings
        └── Limitations
```

and:

```text
GENERATED INFORMATION
        │
        └── Executive Summary
```

The validation therefore checks that:

```text
Generated Narrative
        │
        ▼
Must remain consistent with
        │
        ▼
Authoritative Information
```

The generated narrative may summarize or rephrase deterministic information, but it must not redefine it.

---

# 30. Validation of Information Ownership

Each processing stage has a defined information ownership boundary.

```text
CreditPosition
      │
      │ Structured financial inputs
      ▼
Assessment
      │
      │ Rule results + deterministic status
      ▼
AssessmentAnalysis
      │
      │ Structured findings + risk factors
      │ + limitations + preserved status
      ▼
Report
      │
      │ Executive summary + structured information
      ▼
Application / User
```

Validation verifies that information is not unexpectedly modified as it crosses these boundaries.

In particular:

```text
Assessment Status
       │
       ├── Assessment
       ├── AssessmentAnalysis
       └── Report
```

must remain consistent.

Similarly:

```text
Deterministic Findings
       │
       ├── Assessment
       ├── AssessmentAnalysis
       └── Report
```

must remain traceable throughout the workflow.

---

# 31. Testing the Deterministic–Generative Boundary

The most important architectural tests explicitly verify the boundary between deterministic assessment and generative reporting.

The following properties should be tested:

### Property 1 — LLM independence of assessment

Changing the LLM response must not change:

```text
Assessment.status
Assessment findings
Assessment limitations
```

### Property 2 — LLM availability independence

Removing LLM availability must not prevent:

```text
Assessment
AssessmentAnalysis
```

from being produced.

### Property 3 — Fallback consistency

The fallback report must preserve:

```text
Assessment status
Structured findings
Limitations
```

### Property 4 — Narrative isolation

LLM-generated content must remain within the narrative reporting boundary.

### Property 5 — Deterministic reproducibility

For identical:

```text
CreditPosition
+
Rule Configuration
```

the deterministic assessment must remain identical.

These properties provide stronger architectural evidence than isolated implementation tests.

---

# 32. Test Isolation

Automated testing should remain independent from external generative services.

The preferred testing hierarchy is:

```text
Unit Tests
    │
    ▼
Mock Dependencies
    │
    ▼
Deterministic Results
```

External provider integration should be validated separately.

This separation prevents external service conditions from creating false negatives in tests that are intended to verify application behavior.

It also allows the deterministic assessment engine to be tested under controlled conditions.

---

# 33. Coverage and Quality Indicators

Code coverage can be used as an additional quantitative indicator of test completeness.

Coverage should be monitored across:

* domain models;
* rule implementations;
* configuration;
* assessment services;
* analysis components;
* reporting components;
* LLM integration;
* orchestration;
* error-handling paths.

However, code coverage should not be interpreted as proof of correctness.

A high coverage percentage does not guarantee that:

* all business scenarios are represented;
* all rule interactions are correct;
* all LLM responses are safe;
* all integration failures are detected;
* generated text is semantically correct.

For this reason, coverage should be treated as a supporting verification metric within the broader validation strategy.

The repository should therefore avoid hard-coding a specific coverage percentage in this architectural document unless the value is being reported for a specific validation experiment.

---

# 34. Current Validation Limitations

The current validation establishes functional and architectural correctness at the prototype level, but it does not constitute a complete empirical evaluation of the quality of LLM-generated reports.

Several aspects remain outside the scope of the current validation.

---

## 34.1 Large-Scale LLM Evaluation

The system has not necessarily been evaluated against a statistically representative portfolio containing a large number of real or synthetic credit positions.

A larger evaluation dataset would be required to quantify the robustness of the reporting component across different financial profiles.

---

## 34.2 Hallucination Rate

A systematic benchmark has not yet been established to quantify the frequency of unsupported statements generated by the LLM.

Future validation could explicitly measure:

```text
Unsupported Claims
------------------
Total Generated Statements
```

across a representative test population.

---

## 34.3 Reproducibility of Generated Text

The deterministic assessment is expected to be reproducible.

LLM-generated language, however, may vary between executions.

The current validation therefore distinguishes between:

```text
Deterministic Reproducibility
```

and:

```text
Generative Variability
```

The latter should be evaluated separately if reproducibility of narrative output becomes a project objective.

---

## 34.4 Human Evaluation

The quality of generated executive summaries should ideally be evaluated by domain experts.

Potential evaluation dimensions include:

* factual accuracy;
* completeness;
* clarity;
* professional language;
* relevance;
* consistency with deterministic findings;
* usefulness for a credit analyst;
* preservation of limitations.

Human evaluation is particularly relevant because natural-language quality cannot be fully captured through traditional software testing.

---

## 34.5 Semantic Consistency

The current response validation is intentionally lightweight.

It verifies basic properties such as:

* non-empty output;
* preservation of the expected assessment status.

It does not yet perform a complete semantic comparison between the generated summary and every structured finding.

Future implementations could introduce stronger semantic validation.

---

## 34.6 Performance and Cost

The current validation does not necessarily constitute a systematic benchmark of:

* LLM latency;
* throughput;
* API cost per assessment;
* resource consumption;
* concurrent workload behavior;
* fallback frequency under load.

These aspects become increasingly relevant if the prototype evolves toward production deployment.

---

# 35. Future Validation Extensions

The current validation framework provides a foundation for more advanced experimental evaluation.

A future evaluation pipeline could be structured as:

```text
Large Synthetic Portfolio
          │
          ▼
Deterministic Ground Truth
          │
          ▼
LLM Report Generation
          │
          ▼
Automated Consistency Checks
          │
          ▼
Human Expert Evaluation
          │
          ▼
Quantitative Evaluation
```

Potential future metrics include:

* factual consistency rate;
* unsupported-claim rate;
* finding coverage;
* assessment-status consistency;
* limitation preservation rate;
* contradiction rate;
* human-rated report quality;
* generation latency;
* cost per assessment;
* fallback activation rate;
* external service failure rate.

This would extend the project from functional validation toward an empirical evaluation of the effectiveness and reliability of LLM-assisted credit reporting.

---

# 36. Potential Semantic Validation Architecture

A future version of the system could introduce a stronger validation layer between the LLM and the final report.

The architecture could become:

```text
AssessmentAnalysis
        │
        ▼
LLMReportGenerator
        │
        ▼
Generated Narrative
        │
        ▼
Semantic Validator
        │
        ├── Consistent ─────► Report
        │
        └── Inconsistent
                │
                ▼
             Fallback
```

The semantic validator could compare the generated narrative against the deterministic `AssessmentAnalysis`.

Potential checks could include:

* assessment-status consistency;
* finding coverage;
* unsupported-claim detection;
* numerical consistency;
* limitation preservation;
* contradiction detection;
* recommendation validation.

This would provide a stronger technical guarantee than prompt-level constraints alone.

---

# 37. Validation of Architectural Invariants

The architecture defines several invariants that should remain valid regardless of future implementation changes.

### Invariant 1 — Deterministic assessment authority

```text
Assessment
```

is the authoritative source of the credit assessment.

### Invariant 2 — Status preservation

```text
Assessment.status
=
AssessmentAnalysis.assessment_status
=
Report.assessment_status
```

### Invariant 3 — Finding preservation

```text
Assessment findings
=
Analysis findings
=
Report structured findings
```

### Invariant 4 — Limitation preservation

```text
AssessmentAnalysis.limitations
=
Report.limitations
```

### Invariant 5 — LLM isolation

```text
LLM
→ Narrative generation
```

but not:

```text
LLM
→ Assessment decision
```

### Invariant 6 — Fallback independence

```text
LLM Failure
→ Deterministic Reporting
```

without:

```text
LLM Failure
→ Assessment Failure
```

### Invariant 7 — Deterministic reproducibility

```text
Same Input
+
Same Configuration
→
Same Assessment
```

These invariants represent the principal architectural properties that future refactoring should preserve.

---

# 38. Validation Matrix

The principal validation objectives can be summarized as follows:

| Validation Area          | Expected Property                                               |
| ------------------------ | --------------------------------------------------------------- |
| Individual rules         | Correct deterministic evaluation                                |
| Rule configuration       | Correct interpretation of thresholds and severity policies      |
| Rule discovery           | Rules correctly discovered and registered                       |
| Rule engine              | Correct execution of configured rules                           |
| Assessment service       | Correct deterministic assessment construction                   |
| Assessment status        | Deterministic status calculation                                |
| Analysis agent           | Correct transformation of assessment results                    |
| Assessment analysis      | Deterministic information preserved                             |
| Deterministic reporting  | Reproducible report generation                                  |
| LLM reporting            | Correct integration through `LLMClient`                         |
| LLM response validation  | Invalid responses rejected                                      |
| Assessment integrity     | Status preserved throughout workflow                            |
| Finding integrity        | Deterministic findings preserved                                |
| Limitation integrity     | Deterministic limitations preserved                             |
| LLM failure handling     | External failures detected and isolated                         |
| Deterministic fallback   | Report produced without LLM availability                        |
| Workflow                 | Complete pipeline operates correctly                            |
| Orchestration            | Components executed through the intended workflow               |
| `NOT_EVALUABLE` handling | Non-evaluable rules do not create inappropriate findings        |
| NORMAL scenario          | Correct deterministic and reporting behavior                    |
| ATTENTION scenario       | Correct deterministic and reporting behavior                    |
| CRITICAL scenario        | Correct deterministic and reporting behavior                    |
| Adversarial LLM behavior | Incorrect generated content cannot modify structured assessment |
| External LLM integration | Provider integration validated independently                    |

The status of individual validation activities should be maintained separately from this architectural document so that the document remains stable as the test suite evolves.

---

# 39. Validation Conclusion

The validation strategy is designed to demonstrate that the prototype satisfies its principal functional and architectural requirements.

In particular, the validation must establish that:

1. the deterministic rule engine remains the authoritative source of the assessment;
2. deterministic rules produce reproducible results for identical inputs and configurations;
3. the assessment status is calculated exclusively by deterministic logic;
4. the assessment status is preserved throughout the complete workflow;
5. deterministic findings remain structured and traceable;
6. deterministic limitations remain under application control;
7. the analysis layer does not become a second decision engine;
8. the LLM is restricted to natural-language reporting;
9. invalid LLM responses can be rejected;
10. external LLM failures can be handled through deterministic fallback;
11. fallback reporting does not modify the underlying assessment;
12. automated testing can be performed independently of external LLM availability;
13. representative assessment scenarios can be validated through the complete workflow;
14. the deterministic–generative boundary can be tested explicitly.

The resulting validation framework therefore evaluates not only whether individual software components work correctly, but also whether the overall architecture preserves its most important safety and governance property.

The key validation result is not that the LLM is inherently reliable.

Rather, it is that:

> **The system is designed and tested so that the failure, inconsistency, or unavailability of the generative component cannot alter the authoritative deterministic credit assessment.**

This distinction is fundamental to the architecture of the `credit-assessment-system`.

The deterministic assessment provides:

* reproducibility;
* traceability;
* explicit business logic;
* controlled thresholds;
* controlled severity;
* deterministic classification.

The generative layer provides:

* natural-language generation;
* executive summarization;
* flexible communication of structured results.

The two capabilities therefore remain complementary and independently controllable.

---

# 40. Overall Validation Model

The complete validation philosophy can ultimately be represented as:

```text
                         CREDIT ASSESSMENT SYSTEM
                                   │
                                   ▼
                         Deterministic Assessment
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
             Assessment                  AssessmentAnalysis
                    │                             │
                    │                     Controlled Input
                    │                             │
                    │                             ▼
                    │                    Generative Reporting
                    │                             │
                    │                    ┌────────┴────────┐
                    │                    │                 │
                    │                    ▼                 ▼
                    │              Valid LLM Output     Failure
                    │                    │                 │
                    │                    │                 ▼
                    │                    │       Deterministic Fallback
                    │                    │                 │
                    └────────────────────┴─────────────────┘
                                         │
                                         ▼
                                       Report
```

The validation framework verifies that the information flow remains unidirectional:

```text
Deterministic Assessment
          │
          ▼
Generative Reporting
```

rather than allowing generated content to flow back into the assessment domain:

```text
Deterministic Assessment
          ↕
Generative Reporting
```

Maintaining this one-way boundary is the central architectural requirement of the system and the principal focus of its validation strategy.
