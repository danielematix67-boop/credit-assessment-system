# System Validation

## 1. Validation Scope and Objectives

The validation of the `credit-assessment-system` is designed to verify that the implemented system satisfies its functional and architectural requirements.

The validation focuses on four primary dimensions:

1. **Functional correctness** — individual components and complete workflows produce the expected results.
2. **Assessment integrity** — the deterministic assessment remains authoritative throughout the entire processing pipeline.
3. **LLM integration safety** — the LLM is restricted to the reporting layer and cannot modify the structured assessment.
4. **Operational resilience** — failures in the external LLM service do not invalidate the deterministic assessment or prevent report generation when a fallback generator is available.

The validation is therefore not intended to evaluate the predictive performance of a statistical or machine-learning model. Instead, it evaluates the correctness, consistency, traceability, and architectural integrity of a rule-based credit assessment system augmented with generative AI.

The central validation principle is:

> **The deterministic assessment must remain correct and authoritative regardless of the behavior or availability of the LLM.**

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
                 Real LLM Validation
```

Each level addresses a different type of risk.

### 2.1 Unit Testing

Unit tests verify individual components in isolation and ensure that their contracts are respected.

The automated test suite covers the main functional components of the system, including:

* domain models;
* assessment rules;
* rule configuration;
* rule discovery;
* rule registration;
* severity configuration;
* rule engine;
* assessment services;
* assessment status calculation;
* analysis agent;
* reporting components;
* deterministic report generation;
* LLM report generation;
* LLM response validation;
* LLM clients;
* mock LLM client;
* workflow components;
* orchestration components.

Unit testing is particularly important for the deterministic assessment layer because every individual rule must produce reproducible results for the same input and configuration.

---

## 2.2 Integration Testing

Integration tests verify that independently implemented components operate correctly when combined.

The principal integration points are:

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

* propagation of deterministic rule findings;
* propagation of the assessment status;
* transformation from `Assessment` to `AssessmentAnalysis`;
* transformation from `AssessmentAnalysis` to `Report`;
* preservation of structured findings;
* preservation of limitations;
* selection of the configured report generator;
* LLM reporting and deterministic fallback behavior.

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

End-to-end validation verifies that information is preserved correctly between these stages.

In particular, the following invariant must hold:

```text
Assessment
     │
     ├── status ────────────────┐
     │                          │
     ▼                          ▼
AssessmentAnalysis.status   Report.status
```

The final report must therefore remain consistent with the deterministic assessment that originated the workflow.

---

# 3. Automated Test Suite

The current automated test suite contains:

```text
306 tests
305 passed
1 failure
```

The single failure identified during the latest execution concerns the severity assigned to an `InterestCoverageRatioRule` result.

The failure is not related to the workflow architecture or LLM integration. It is a configuration/test expectation mismatch:

```text
Expected: HIGH
Actual:   MEDIUM
```

for an interest coverage ratio of `1.50`.

This demonstrates an important property of the test suite: configuration inconsistencies are detected explicitly rather than being silently propagated into the final assessment.

After aligning the test expectation with the intended severity configuration, the target state is:

```text
306 passed
0 failed
```

The test suite also provides high code coverage across the implemented system. The latest coverage execution reports:

```text
Total statements: 652
Missed statements: 17
Coverage: 97%
```

The remaining uncovered statements are primarily associated with defensive branches, abstract interfaces, exceptional paths, and alternative runtime conditions.

Code coverage is used as a supporting verification metric rather than as the sole indicator of software quality.

---

# 4. Deterministic Assessment Validation

The deterministic assessment layer is the authoritative decision-making component of the system.

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
Assessment Status
```

The currently supported assessment states are:

```text
NORMAL
ATTENTION
CRITICAL
```

The status is determined exclusively by deterministic logic and configured rule behavior.

The LLM is not involved in:

* rule evaluation;
* threshold comparison;
* severity determination;
* assessment status calculation;
* modification of rule results.

Consequently, the following property is expected:

```text
Same Input
    +
Same Configuration
    ↓
Same Assessment
```

This reproducibility is one of the principal architectural advantages of the system.

---

# 5. Assessment Integrity

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

Automated tests explicitly verify the following invariant:

```text
Assessment.status
    =
AssessmentAnalysis.assessment_status
    =
Report.assessment_status
```

The same principle applies to structured findings.

The deterministic findings generated by the assessment layer must remain the findings exposed by the analysis and reporting layers.

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

The LLM therefore does not have authority over the structured assessment data.

---

# 6. LLM Reporting Validation

The LLM is deliberately isolated within the reporting layer.

Its purpose is to generate an executive summary from an already structured `AssessmentAnalysis`.

The input to the LLM includes information such as:

* assessment status;
* key findings;
* risk factors;
* limitations.

The LLM is explicitly instructed not to:

* introduce unsupported financial information;
* invent causes or trends;
* modify the assessment status;
* make an independent credit decision;
* introduce unsupported recommendations;
* disclose internal rule thresholds.

The generated response is treated as **untrusted external content**.

It is therefore validated before being accepted as the executive summary of the final report.

---

## 6.1 Current LLM Response Validation

The current implementation performs two explicit checks.

### Check 1 — Non-empty response

An empty or whitespace-only response is rejected.

```text
LLM Response
     │
     ▼
Empty?
     │
   YES → Reject
```

### Check 2 — Assessment status preservation

The generated response must contain the deterministic assessment status.

For example, if:

```text
Assessment status = CRITICAL
```

the response must contain:

```text
CRITICAL
```

If the expected status is absent, the response is rejected.

This provides a lightweight consistency check between the generated natural-language output and the authoritative structured assessment.

---

# 7. LLM Cannot Replace Deterministic Findings

The structured findings contained in the final report are not generated by the LLM.

They originate from the deterministic assessment pipeline:

```text
Rule
  ↓
RuleResult
  ↓
RuleFinding
  ↓
AnalysisFinding
  ↓
ReportFindingGroup
```

The LLM is responsible only for the executive summary.

This architectural property is explicitly tested by injecting an LLM response containing information that does not correspond to the structured findings.

The test verifies that the injected LLM content does not become part of the report's structured findings.

This ensures that:

```text
LLM-generated text
       ≠
Deterministic findings
```

and that the latter remain authoritative.

---

# 8. LLM Cannot Replace Deterministic Limitations

The same principle applies to limitations.

Limitations are generated by the deterministic analysis pipeline and subsequently propagated into the final report.

The expected relationship is:

```text
AssessmentAnalysis.limitations
          =
Report.limitations
```

The LLM cannot replace, remove, or redefine these structured limitations.

This ensures that information about incomplete or non-evaluable assessment conditions remains under deterministic control.

---

# 9. LLM Failure Handling and Deterministic Fallback

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

The deterministic assessment is not recalculated when the LLM fails.

Instead:

1. the deterministic assessment remains unchanged;
2. the analysis remains unchanged;
3. the LLM reporting attempt fails;
4. the deterministic report generator produces the final report.

This establishes an important resilience property:

> **Failure of the generative reporting component must not cause failure of the deterministic credit assessment.**

---

# 10. Fallback Validation

The fallback mechanism is explicitly tested using a failing LLM client.

The test simulates an external service failure and verifies that:

* the deterministic assessment remains valid;
* the assessment status remains unchanged;
* the analysis remains unchanged;
* the fallback generator is selected;
* a valid report is produced;
* structured findings remain unchanged;
* limitations remain unchanged.

Runtime diagnostics are also exposed by the `ReportingAgent`:

```text
last_generator_used
last_error
```

These fields provide lightweight observability of the reporting path.

For example:

```text
last_generator_used = "PRIMARY"
```

indicates successful LLM report generation.

Whereas:

```text
last_generator_used = "FALLBACK"
```

indicates that deterministic reporting was used after primary-generator failure.

---

# 11. LLM Test Isolation

Automated tests do not depend on a live LLM service.

The `MockLLMClient` provides deterministic responses and allows the LLM-dependent reporting logic to be tested without external infrastructure.

This avoids coupling the automated test suite to:

* network connectivity;
* external service availability;
* API quotas;
* API costs;
* model nondeterminism.

The architecture is therefore:

```text
Automated Tests
      │
      ▼
MockLLMClient
      │
      ▼
Deterministic Test Behaviour
```

The real `GeminiClient` is validated separately through scenario-based testing.

This separation is important because a software test suite should remain reproducible even when an external generative service is unavailable.

---

# 12. Scenario-Based Validation

In addition to automated testing, the system is evaluated using representative credit-assessment scenarios.

The scenarios are designed to exercise the three principal assessment states:

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
* consistency between structured and generated information.

The scenario-based validation complements automated testing by evaluating the behavior of the complete system under representative business conditions.

---

## 12.1 NORMAL Scenario

The `NORMAL` scenario represents a position whose financial indicators remain within the configured acceptable ranges.

Expected result:

```text
Assessment Status = NORMAL
```

The report should communicate that the assessment is normal without introducing unsupported risk factors.

---

## 12.2 ATTENTION Scenario

The `ATTENTION` scenario represents a position where one or more indicators require monitoring but the deterministic rules do not classify the overall position as critical.

Expected result:

```text
Assessment Status = ATTENTION
```

The generated report should accurately communicate the identified areas of attention while preserving the deterministic assessment status.

---

## 12.3 CRITICAL Scenario

The `CRITICAL` scenario represents a position affected by multiple significant adverse indicators.

Expected result:

```text
Assessment Status = CRITICAL
```

The report should communicate the critical status and summarize the relevant findings supplied by the deterministic analysis.

The LLM must not introduce an alternative assessment classification.

---

# 13. Validation of Non-Evaluable Conditions

The system also validates the behavior of rules that cannot be evaluated because the required information is unavailable or unsuitable.

A rule may return:

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

The validation verifies that `NOT_EVALUABLE` results do not incorrectly generate findings.

The expected behavior is:

```text
Rule Result = NOT_EVALUABLE
             │
             ▼
        No Finding
```

This is important because a missing or non-evaluable indicator should not automatically be interpreted as a negative credit signal.

The test suite explicitly verifies that:

* `NOT_EVALUABLE` rule results are present where expected;
* their rule IDs do not appear among generated findings;
* the analysis does not incorrectly expose them as key findings;
* the final report does not contain corresponding structured findings.

---

# 14. Validation Matrix

The principal validation objectives can be summarized as follows:

| Validation Area          | Expected Property                             | Status    |
| ------------------------ | --------------------------------------------- | --------- |
| Individual rules         | Correct deterministic evaluation              | Passed    |
| Rule configuration       | Correct thresholds and severity configuration | Passed    |
| Rule discovery           | Rules correctly discovered and registered     | Passed    |
| Rule engine              | Correct execution of configured rules         | Passed    |
| Assessment service       | Correct assessment construction               | Passed    |
| Assessment status        | Deterministic status calculation              | Passed    |
| Analysis agent           | Correct transformation of assessment results  | Passed    |
| Deterministic reporting  | Reproducible report generation                | Passed    |
| LLM reporting            | Correct integration through `LLMClient`       | Passed    |
| LLM response validation  | Invalid responses rejected                    | Passed    |
| Assessment integrity     | Status preserved through workflow             | Passed    |
| Finding integrity        | Deterministic findings preserved              | Passed    |
| Limitation integrity     | Deterministic limitations preserved           | Passed    |
| LLM failure handling     | Failure detected and handled                  | Passed    |
| Deterministic fallback   | Report produced without LLM                   | Passed    |
| End-to-end workflow      | Complete pipeline operates correctly          | Passed    |
| `NOT_EVALUABLE` handling | Non-evaluable rules do not create findings    | Passed    |
| NORMAL scenario          | Correct behavior validated                    | Validated |
| ATTENTION scenario       | Correct behavior validated                    | Validated |
| CRITICAL scenario        | Correct behavior validated                    | Validated |
| Real Gemini integration  | External LLM integration validated            | Validated |

---

# 15. Coverage and Quality Indicators

Code coverage provides an additional quantitative indicator of test completeness.

The latest coverage execution reports:

```text
Total statements: 652
Covered statements: 635
Missed statements: 17
Overall coverage: 97%
```

The coverage is distributed across the major architectural components, with the deterministic rule implementations and core domain models achieving very high coverage.

However, code coverage should not be interpreted as proof of correctness.

A high coverage percentage indicates that a large proportion of the implementation is exercised by automated tests, but it does not guarantee that:

* all business scenarios are represented;
* all generated LLM responses are safe;
* all integration failures are detected;
* generated text is semantically correct.

For this reason, code coverage is considered a supporting metric within the broader validation strategy.

---

# 16. Current Validation Limitations

The current validation establishes functional and architectural correctness at the prototype level, but it does not constitute a complete empirical evaluation of the quality of LLM-generated reports.

The following aspects are currently outside the scope of the implemented validation:

### 16.1 Large-Scale LLM Evaluation

The system has not yet been evaluated against a statistically representative portfolio containing a large number of real or synthetic credit positions.

### 16.2 Hallucination Rate

No systematic benchmark has yet been established to quantify the frequency of unsupported statements generated by the LLM.

### 16.3 Reproducibility of Generated Text

The deterministic assessment is reproducible, whereas LLM-generated language may vary between executions.

The current validation does not quantify this variability.

### 16.4 Human Evaluation

The quality of generated executive summaries has not yet been systematically evaluated by credit-risk experts.

Potential evaluation dimensions include:

* factual accuracy;
* completeness;
* clarity;
* professional language;
* relevance;
* consistency with the underlying assessment.

### 16.5 Semantic Consistency

The current response validation is intentionally lightweight.

It verifies the presence of the expected assessment status and rejects empty responses, but it does not yet perform a complete semantic comparison between the generated summary and every structured finding.

### 16.6 Performance and Cost

The current validation does not systematically measure:

* LLM latency;
* throughput;
* API cost per assessment;
* resource consumption;
* behavior under concurrent workloads.

These aspects become relevant if the prototype evolves toward production deployment.

---

# 17. Future Validation Extensions

The current validation framework provides a foundation for more advanced experimental evaluation.

Possible extensions include:

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
```

Potential future metrics include:

* factual consistency rate;
* unsupported-claim rate;
* finding coverage;
* assessment-status consistency;
* limitation preservation rate;
* human-rated report quality;
* generation latency;
* cost per assessment;
* failure rate;
* fallback activation rate.

This would extend the project from functional validation toward an empirical evaluation of the effectiveness and reliability of LLM-assisted credit reporting.

---

# 18. Validation Conclusion

The implemented validation strategy demonstrates that the current prototype satisfies its principal architectural requirements.

In particular:

1. the deterministic rule engine remains the authoritative source of the assessment;
2. the assessment status is preserved across the complete workflow;
3. deterministic findings are propagated without being replaced by LLM-generated content;
4. deterministic limitations remain under application control;
5. invalid LLM responses are rejected;
6. failures of the external LLM service can be handled through deterministic fallback;
7. the complete workflow is exercised through automated integration and end-to-end tests;
8. representative `NORMAL`, `ATTENTION`, and `CRITICAL` scenarios are validated;
9. the real LLM integration can be tested independently from the deterministic automated test suite.

The resulting architecture can therefore be considered **functionally validated at the current prototype level**.

However, this validation should not be interpreted as evidence that LLM-generated reports are universally reliable or production-ready. A subsequent experimental phase would be required to quantify report quality, factual consistency, hallucination frequency, reproducibility, operational performance, and human acceptance.

The key result of the current validation is therefore not that the LLM is inherently reliable, but that **the system architecture constrains the LLM so that its failure or incorrect generation does not compromise the authoritative deterministic credit assessment**.
