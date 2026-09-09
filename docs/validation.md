# System Validation

## 1. Purpose

The validation strategy verifies the functional correctness, architectural integrity, and resilience of the `credit-assessment-system`.

The system is a deterministic, rule-based credit assessment application with an optional LLM reporting layer. Validation therefore focuses on a central architectural invariant:

> **The deterministic assessment is the source of truth. The LLM can generate narrative content, but it cannot determine, modify, or override the structured credit assessment.**

The validation strategy does not evaluate the predictive performance of a statistical or machine-learning model. It validates the behavior of the implemented rule engine, assessment workflow, reporting layer, configuration, and LLM integration.

---

## 2. Validation Pyramid

The project uses multiple levels of automated validation:

```text
                    SYSTEM VALIDATION
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Unit Tests     Integration Tests   Workflow Tests
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    LLM / Fallback Tests
                           │
                           ▼
                    CI Quality Gates
```

| Level | Main objective |
|---|---|
| Unit | Validate individual components and business rules |
| Integration | Validate interactions between application layers |
| Workflow | Validate the complete assessment-to-report pipeline |
| LLM / fallback | Validate provider integration and failure handling |
| CI | Enforce repeatable quality gates |

---

# 3. Core Architectural Invariants

### 3.1 Deterministic decision authority

The assessment status is calculated from deterministic rule results and configured assessment logic.

```text
CreditPosition
      ↓
Rule Engine
      ↓
Rule Results
      ↓
Assessment Status
```

The LLM is not part of this decision path.

### 3.2 Status propagation

The deterministic status must be preserved throughout the workflow:

```text
Assessment.status
       ↓
AssessmentAnalysis.assessment_status
       ↓
Report.assessment_status
```

### 3.3 Structured finding integrity

Structured findings originate from deterministic rule evaluation and are propagated to the analysis and reporting layers.

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

The LLM does not create the structured finding collection.

### 3.4 Reporting independence

Different reporting strategies may produce different natural-language summaries, but they operate on the same deterministic `AssessmentAnalysis`.

```text
                 AssessmentAnalysis
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
 DeterministicReportGenerator   LLMReportGenerator
              │                     │
              └──────────┬──────────┘
                         ▼
                       Report
```

The assessment status and structured findings remain application-controlled.

---

# 4. Unit Testing

Unit tests validate individual classes and business contracts in isolation.

The main areas include:

- domain models;
- rule status and severity types;
- severity policy;
- rule configuration;
- YAML configuration loading;
- rule registration and discovery;
- individual assessment rules;
- rule engine;
- assessment service;
- status calculation;
- analysis agent;
- deterministic report generation;
- LLM report generation;
- LLM client abstractions;
- mock LLM client;
- reporting agent;
- workflow components;
- orchestration components.

For deterministic rules, the fundamental property is:

```text
Same Input
    +
Same Configuration
    ↓
Same RuleResult
```

Unit tests should therefore cover normal evaluations, triggered conditions, boundary values, and non-evaluable inputs where applicable.

---

# 5. Rule Validation

Each rule produces a structured `RuleResult` for a given evaluation.

A rule result contains information including:

- rule identifier;
- rule name;
- category;
- status;
- evaluated value, when available;
- configured threshold;
- severity;
- reason.

The supported statuses distinguish three situations:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

This distinction is important for credit-risk assessment because missing or unsuitable data must not automatically be interpreted as a negative credit signal.

## 5.1 Threshold validation

Tests verify that rule thresholds are applied according to the configured rule definition and that boundary conditions behave consistently with the rule implementation.

## 5.2 Severity validation

Severity is resolved through the configured `SeverityPolicy` when a numeric value is available.

The system supports directional severity evaluation, including:

```text
LOWER_IS_WORSE
HIGHER_IS_WORSE
```

Configured severity thresholds are therefore tested independently from the primary trigger threshold.

## 5.3 Non-evaluable validation

A rule that cannot be evaluated returns `NOT_EVALUABLE` rather than incorrectly returning `TRIGGERED` or `NOT_TRIGGERED`.

The assessment service creates findings only when the comment engine returns a comment; the comment engine generates comments for triggered rules.

Conceptually:

```text
NOT_EVALUABLE
      ↓
No triggered finding
```

---

# 6. Rule Configuration Validation

Rule behavior is separated into deterministic implementation logic and external YAML configuration.

The configuration loader validates structural and semantic requirements such as:

- required fields;
- unique rule identifiers;
- supported severity values;
- supported severity directions;
- valid numeric thresholds;
- valid severity-threshold definitions.

The intended dependency is:

```text
config/rules.yaml
        ↓
RuleConfigLoader
        ↓
RuleConfig
        ↓
Rule Registry
        ↓
Concrete Rule
```

This separation allows policy parameters to change without modifying the rule-engine infrastructure.

---

# 7. Assessment Service Validation

`AssessmentService` orchestrates the deterministic assessment stage.

Its processing sequence is:

```text
CreditPosition
      ↓
RuleEngine.evaluate()
      ↓
RuleResults
      ↓
CommentEngine
      ↓
RuleFindings
      ↓
StatusCalculator
      ↓
Assessment
```

Validation verifies that:

- rule results are preserved;
- comments are generated only where applicable;
- findings reference the originating rule result;
- the overall status is calculated from deterministic rule results;
- the returned `Assessment` contains the expected position identifier.

The assessment service does not invoke an LLM.

---

# 8. Analysis Layer Validation

The `AnalysisAgent` transforms an `Assessment` into an `AssessmentAnalysis`.

```text
Assessment
    ↓
AnalysisAgent
    ↓
AssessmentAnalysis
```

The analysis layer is not an alternative decision engine.

Validation focuses on preservation of the deterministic assessment and on the construction of analysis-level information such as key findings, risk factors, and limitations.

The critical property is:

```text
Assessment.status
        =
AssessmentAnalysis.assessment_status
```

The analysis object is then used as the controlled input to the reporting layer.

---

# 9. Reporting Validation

The reporting architecture separates report generation from assessment logic.

The application supports a deterministic generator and optional LLM-backed generation with fallback.

## 9.1 Deterministic reporting

`DeterministicReportGenerator` provides a report-generation path without an external LLM dependency.

Validation verifies that it creates a report from the supplied `AssessmentAnalysis` while preserving the structured assessment information.

## 9.2 LLM reporting

`LLMReportGenerator` uses an injected `LLMClient` to generate narrative content from deterministic analysis data.

The prompt explicitly constrains the model to narrative generation. The model is not asked to calculate a new assessment or determine the credit status.

The LLM therefore operates on:

```text
AssessmentAnalysis
       ↓
Prompt Builder
       ↓
LLM Client
       ↓
Generated Narrative
```

rather than directly on the rule engine.

---

# 10. LLM Response Validation

The current implementation performs a deliberately narrow validation of the raw LLM response.

The response validator checks that the generated response is not empty or whitespace-only. A response that fails this check is rejected.

```text
LLM Response
      ↓
_is response usable?_
      │
   ┌──┴──┐
   │     │
  No    Yes
   │     │
   ▼     ▼
Invalid  Narrative
         accepted
```

### Important implementation boundary

The current implementation **does not perform string-based validation of the assessment status inside the LLM response**.

It does not search the generated narrative for `NORMAL`, `ATTENTION`, or `CRITICAL`, and it does not reject a response merely because those words are absent.

This is an important distinction from semantic validation. Structured assessment status remains outside the generated narrative and is controlled by application logic.

The application adds the deterministic assessment status to the executive-summary construction, while the structured `Report.assessment_status` remains application-controlled.

This avoids brittle natural-language matching at the decision boundary.

---

# 11. Deterministic Status Protection

The final report's structured assessment status is application-controlled.

Conceptually:

```text
AssessmentAnalysis.assessment_status
                │
                ├──────────────► Report.assessment_status
                │
                └──────────────► Executive-summary context
                                      │
                                      ▼
                                     LLM
```

The LLM therefore cannot directly change the structured `Report.assessment_status`.

The executive summary is constructed with the deterministic status available to the reporting layer, so the generated narrative is not the source of truth for the classification.

---

# 12. Deterministic Findings and Limitations

Structured findings and limitations remain under application control.

The reporting layer receives them from `AssessmentAnalysis`; they are not reconstructed from the LLM response.

```text
Deterministic Assessment
          ↓
AssessmentAnalysis
          ├── assessment_status
          ├── key_findings
          ├── risk_factors
          └── limitations
                    ↓
                 Reporting
```

The LLM generates narrative content from this controlled information. It does not write back into the structured assessment.

Consequently, an unsupported statement generated by the model does not become a new `RuleFinding`, does not change the structured assessment status, and does not replace the application's structured limitations.

---

# 13. Fallback and Resilience Validation

The reporting agent supports a primary report generator and an optional deterministic fallback.

```text
                 ReportingAgent
                       │
              Primary Generator
                       │
                ┌──────┴──────┐
                │             │
              Success       Failure
                │             │
                ▼             ▼
             Report      Deterministic
                           Fallback
                              │
                              ▼
                            Report
```

Validation covers failures such as:

- LLM client errors;
- invalid/empty generated responses;
- exceptions raised by the primary generator;
- successful fallback execution;
- fallback failure handling.

The key resilience property is:

> **Failure of the optional LLM reporting path must not invalidate the deterministic assessment.**

The reporting agent also records the generator used and the latest reporting error, supporting execution traceability.

---

# 14. LLM Provider Abstraction

LLM access is abstracted behind an `LLMClient` interface.

The architecture supports provider-specific implementations such as Gemini and Ollama, as well as a mock client for testing.

```text
                 LLMClient
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Gemini      Ollama       Mock
```

Validation focuses on the contract between the reporting generator and the client rather than on the internal implementation of a particular provider.

Provider failures are handled by the reporting layer and can activate deterministic fallback.

---

# 15. Workflow and Orchestration Validation

The complete workflow connects the deterministic assessment, analysis, and reporting layers.

```text
CreditPosition
      ↓
AssessmentService
      ↓
Assessment
      ↓
AnalysisAgent
      ↓
AssessmentAnalysis
      ↓
ReportingAgent
      ↓
ReportGenerator
      ↓
Report
```

Workflow and orchestration tests verify that dependencies are correctly constructed and that data is propagated through the complete processing chain.

The primary end-to-end invariant is:

```text
Assessment.status
      =
AssessmentAnalysis.assessment_status
      =
Report.assessment_status
```

The structured assessment information remains independent of the selected reporting strategy.

---

# 16. Test Isolation

External LLM availability is not required for the standard automated test suite.

The project provides a mock LLM client and separates tests requiring a live Ollama service through the `ollama` pytest marker.

The default pytest configuration excludes Ollama-dependent tests:

```text
pytest
  ↓
standard test suite
  ↓
no live Ollama dependency
```

This keeps CI deterministic while allowing provider-specific integration tests to be executed explicitly when the required service is available.

---

# 17. CI Quality Gates

The GitHub Actions pipeline enforces the main engineering validation gates.

The current CI workflow runs against Python 3.13 and 3.14 and performs:

```text
Install dependencies
        ↓
Ruff linting
        ↓
MyPy strict type checking
        ↓
Pytest
        ↓
Coverage threshold
```

The test command enforces a minimum coverage of **95%** for the `src` package.

These checks provide a repeatable baseline for pushes to `main` and pull requests targeting `main`.

---

# 18. Validation Matrix

| Area | Validation mechanism | Expected property |
|---|---|---|
| Rule evaluation | Unit tests | Deterministic `RuleResult` |
| Thresholds | Rule tests | Configured thresholds are applied correctly |
| Severity | Severity-policy tests | Direction and severity thresholds are respected |
| Non-evaluable inputs | Rule/service tests | `NOT_EVALUABLE` is handled explicitly |
| Configuration | Config tests | Invalid configuration is rejected |
| Rule registry | Registry tests | Correct rule implementation is discovered |
| Assessment service | Unit/integration tests | Results, findings, and status are composed correctly |
| Analysis | Agent tests | Deterministic status and findings remain authoritative |
| Deterministic reporting | Generator tests | Report is produced without external LLM dependency |
| LLM reporting | Generator/client tests | Narrative is generated from controlled analysis data |
| LLM response validation | Generator tests | Empty/whitespace output is rejected |
| Fallback | Reporting-agent tests | Primary failure can fall back to deterministic reporting |
| Workflow | Integration/E2E tests | Data is propagated through the full pipeline |
| Type safety | MyPy strict | Source code satisfies static typing constraints |
| Code quality | Ruff | Configured lint rules pass |
| Coverage | Pytest-Cov | `src` coverage remains at or above 95% |

---

# 19. Validation Boundaries and Limitations

The automated validation strategy does not prove that an external LLM will always produce factually correct or semantically perfect prose.

Generative output remains probabilistic and should therefore be treated as untrusted content.

The architecture mitigates this risk by keeping the LLM outside the deterministic decision path and by retaining structured assessment information under application control.

The current response validator is intentionally limited to basic response usability. It does not attempt to prove semantic equivalence between generated prose and structured findings through natural-language parsing.

This is preferable to introducing brittle string-matching logic into the decision boundary.

Future enhancements may include stronger observability, structured LLM outputs, additional schema validation, and provider-specific integration testing, provided that these enhancements preserve the deterministic assessment boundary.

---

# 20. Summary

The validation strategy is built around a simple architectural principle:

```text
Deterministic Assessment
          │
          ├── Source of Truth
          │
          ▼
   AssessmentAnalysis
          │
          ▼
   Reporting Layer
          │
     ┌────┴────┐
     ▼         ▼
Deterministic  LLM
   Report     Narrative
     │         │
     └────┬────┘
          ▼
        Report
```

The deterministic rule engine remains responsible for assessment logic, status calculation, and structured findings.

The LLM is an optional reporting component. Its failure does not invalidate the assessment, and its generated narrative does not become the source of truth for structured credit information.

This separation is the principal architectural property validated by the project's automated tests and CI quality gates.
