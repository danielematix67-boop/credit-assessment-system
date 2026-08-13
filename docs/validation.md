# System Validation

## 1. Validation Objectives

The validation process aims to verify that the credit assessment system behaves consistently with its architectural principles and functional requirements.

The main objectives are:

* verify the correctness of the deterministic credit assessment engine;
* verify the consistency of the workflow across all processing stages;
* verify the integration of the LLM-based reporting component;
* ensure that the LLM cannot modify the deterministic assessment;
* verify that invalid LLM responses are rejected;
* verify that the system remains operational when the LLM service is unavailable;
* verify the behavior of the system across different assessment scenarios.

The validation focuses on **functional correctness, architectural integrity, and resilience** rather than on evaluating the predictive performance of a statistical or machine-learning model.

---

## 2. Validation Strategy

The system is validated at multiple levels.

```text
Unit Testing
     ↓
Integration Testing
     ↓
End-to-End Testing
     ↓
LLM Integration Testing
     ↓
Scenario-Based Validation
```

Each level addresses a different aspect of system behavior.

### 2.1 Unit Testing

Unit tests verify individual components in isolation.

The test suite covers:

* domain models;
* assessment rules;
* rule configuration;
* rule discovery and registration;
* rule engine;
* assessment services;
* assessment status calculation;
* analysis agent;
* reporting components;
* deterministic report generation;
* LLM report generation;
* LLM response validation;
* LLM clients and mock clients.

The purpose of unit testing is to ensure that individual components behave according to their defined contracts.

---

### 2.2 Integration Testing

Integration tests verify the interaction between multiple components.

The main integration points include:

* assessment service and rule engine;
* assessment service and analysis agent;
* analysis agent and reporting agent;
* deterministic reporting;
* LLM-based reporting;
* workflow construction;
* complete assessment workflow execution.

These tests ensure that independently tested components also operate correctly when combined.

---

### 2.3 End-to-End Testing

End-to-end tests execute the complete assessment workflow starting from a `CreditPosition` and ending with a generated `Report`.

The main processing flow is:

```text
CreditPosition
      ↓
Assessment Service
      ↓
Deterministic Assessment
      ↓
Analysis Agent
      ↓
AssessmentAnalysis
      ↓
Reporting Agent
      ↓
Report
```

The end-to-end tests verify that:

* the original position is preserved;
* the assessment is correctly generated;
* the assessment status is propagated through the workflow;
* the analysis is generated correctly;
* the final report is generated;
* structured assessment information remains consistent across stages.

---

### 2.4 LLM Integration Testing

The LLM component is tested separately from the deterministic assessment logic.

A mock LLM client is used during automated tests to provide deterministic and reproducible responses.

A separate integration scenario uses the actual `GeminiClient` to verify the behavior of the complete workflow with a real LLM service.

This distinction allows the system to maintain deterministic automated tests while still providing a mechanism for validating the real LLM integration.

---

# 3. Deterministic Assessment Validation

The deterministic assessment engine is the authoritative component responsible for determining the credit assessment status.

The assessment status is calculated exclusively from the structured financial information and the configured assessment rules.

The possible assessment states are:

```text
NORMAL
ATTENTION
CRITICAL
```

The LLM is not involved in this decision.

The validation therefore verifies that:

```text
Financial Data
      ↓
Deterministic Rules
      ↓
Assessment Status
```

is independent from:

```text
Assessment Analysis
      ↓
LLM Report Generation
```

This separation is a fundamental architectural property of the system.

---

# 4. LLM Reporting Validation

The LLM is used exclusively as a reporting component.

Its responsibility is to transform the structured assessment analysis into a natural-language executive summary.

The LLM receives:

* assessment status;
* key findings;
* risk factors;
* limitations.

The LLM does not receive authority to modify the underlying assessment.

The generated response is validated before being converted into a `Report`.

The validation checks include:

* non-empty response;
* presence of the expected assessment status;
* presence of required key findings;
* presence of required risk factors.

Invalid responses are rejected through explicit validation errors.

This prevents an LLM response from silently omitting critical information.

---

# 5. Assessment Integrity

A central validation requirement is that the LLM must not alter the deterministic assessment.

The workflow preserves the assessment status through all stages:

```text
Assessment.status
       │
       ▼
AssessmentAnalysis.assessment_status
       │
       ▼
Report.assessment_status
```

Automated integration tests explicitly verify that these values remain consistent.

The following invariant is therefore expected:

```text
Report.assessment_status
    =
AssessmentAnalysis.assessment_status
    =
Assessment.status
```

The LLM is responsible only for generating the natural-language report content.

This establishes a clear separation between:

* **decision logic**, which is deterministic;
* **reporting logic**, which may use an LLM.

---

# 6. LLM Failure and Deterministic Fallback

The reporting architecture includes a deterministic fallback mechanism.

The `ReportingAgent` first attempts to generate the report using the configured primary report generator.

When the primary generator fails, the agent invokes the fallback generator if one is configured.

The resulting flow is:

```text
                 ┌──────────────────┐
                 │ Reporting Agent  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ LLM Report       │
                 │ Generator        │
                 └────────┬─────────┘
                          │
                   Success│Failure
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

The fallback mechanism has been explicitly tested using an LLM client that raises an exception.

The test verifies that:

* the deterministic assessment remains valid;
* the assessment status is preserved;
* the analysis remains consistent;
* a valid report is still produced;
* the system does not depend exclusively on the availability of the LLM service.

This provides an additional resilience mechanism for the reporting layer.

---

# 7. Scenario-Based Validation

The system has also been evaluated using three representative financial scenarios.

The scenarios correspond to the three possible assessment states:

```text
NORMAL
ATTENTION
CRITICAL
```

Each scenario is processed through the complete workflow using the actual `GeminiClient`.

The following elements are inspected:

* assessment status;
* key findings;
* risk factors;
* limitations;
* generated executive summary.

---

## 7.1 NORMAL Scenario

The normal scenario represents a position whose financial indicators remain within the configured acceptable ranges.

Expected behavior:

```text
Assessment Status: NORMAL
```

The generated report should communicate the normal assessment without introducing additional unsupported concerns.

---

## 7.2 ATTENTION Scenario

The attention scenario represents a position with one or more indicators requiring monitoring, while the overall situation does not meet the conditions for a critical assessment.

Expected behavior:

```text
Assessment Status: ATTENTION
```

The report should describe the identified findings and clearly distinguish them from any limitations.

---

## 7.3 CRITICAL Scenario

The critical scenario represents a position affected by multiple significant negative indicators.

Expected behavior:

```text
Assessment Status: CRITICAL
```

The generated report should communicate the critical status and describe the relevant findings, risk factors, and limitations provided by the deterministic analysis.

---

# 8. Validation Results

The current validation activities demonstrate the following properties:

| Validation Property                 | Result    |
| ----------------------------------- | --------- |
| Individual rule behavior            | Passed    |
| Rule engine behavior                | Passed    |
| Assessment status calculation       | Passed    |
| Analysis generation                 | Passed    |
| Deterministic reporting             | Passed    |
| LLM reporting integration           | Passed    |
| LLM response validation             | Passed    |
| Assessment status preservation      | Passed    |
| Structured information preservation | Passed    |
| LLM failure handling                | Passed    |
| Deterministic fallback              | Passed    |
| End-to-end workflow                 | Passed    |
| NORMAL scenario                     | Validated |
| ATTENTION scenario                  | Validated |
| CRITICAL scenario                   | Validated |
| Real Gemini integration             | Validated |

The automated test suite currently provides coverage across the main components of the system, while the scenario-based execution provides an additional validation layer for the real LLM integration.

---

# 9. Current Limitations

The current validation demonstrates functional and architectural correctness, but it does not constitute a complete empirical evaluation of LLM quality.

In particular, the current validation does not systematically measure:

* factual accuracy across a large dataset;
* consistency across repeated LLM generations;
* hallucination frequency;
* report quality according to human reviewers;
* semantic similarity between structured findings and generated reports;
* performance across a statistically representative portfolio;
* latency and operational cost of LLM generation.

These aspects are outside the scope of the current functional validation and may be addressed in a subsequent experimental evaluation.

---

# 10. Validation Conclusion

The validation activities confirm that the implemented architecture preserves the intended separation between deterministic credit assessment and LLM-based reporting.

The deterministic assessment engine remains the authoritative decision-making component, while the LLM operates exclusively within the reporting layer.

The implemented validation strategy also demonstrates that:

1. deterministic assessment results are preserved throughout the workflow;
2. structured findings and risk factors are explicitly validated;
3. invalid LLM responses are rejected;
4. LLM failures can be handled through deterministic fallback;
5. the complete workflow operates across `NORMAL`, `ATTENTION`, and `CRITICAL` scenarios.

The system can therefore be considered **functionally validated at the current prototype level**, while further empirical evaluation can be performed to assess the quality and consistency of LLM-generated reports.
