# System Validation

## 1. Purpose

The validation strategy verifies the functional correctness, architectural integrity and resilience of the `credit-assessment-system`.

The application is deterministic at the assessment layer and optional/AI-assisted at the reporting layer. The central invariant is:

> **The deterministic assessment is the source of truth. The LLM can generate narrative content, but it cannot determine, modify or override the structured credit assessment.**

Validation therefore covers input integrity, rules, configuration, assessment, analysis, reporting, LLM integration, narrative grounding, fallback behavior, workflow propagation, execution metadata and CI quality gates.

---

## 2. Validation Pyramid

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
                 LLM / Grounding Tests
                           │
                           ▼
                    CI Quality Gates
```

| Level | Main objective |
|---|---|
| Unit | Validate individual components, validation rules and business rules |
| Integration | Validate interactions between application layers |
| Workflow | Validate the complete assessment-to-report pipeline |
| LLM / grounding | Validate narrative constraints, evidence preservation and provider behavior |
| CI | Enforce repeatable lint, type and coverage gates |

---

# 3. Core Architectural Invariants

## 3.1 Deterministic decision authority

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

## 3.2 Input validation precedes assessment

```text
CreditPosition
      ↓
CreditPositionValidator
   /             \\
valid           invalid
  ↓                 ↓
Rule Engine      Reject input
```

Structural validation is performed before rule evaluation. This prevents malformed objects, non-numeric values and non-finite numeric values from entering the deterministic assessment pipeline.

The validator checks:

- valid `CreditPosition` type;
- non-empty `position_id`;
- numeric financial fields or `None`;
- rejection of boolean values in numeric fields;
- finite numeric values only, rejecting `NaN` and positive/negative infinity.

The validator deliberately does not impose business-specific sign constraints. Those semantics belong to the corresponding credit rule.

## 3.3 Status propagation

The deterministic status is preserved through the workflow:

```text
Assessment.status
       ↓
AssessmentAnalysis.assessment_status
       ↓
Report.assessment_status
```

## 3.4 Structured finding integrity

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

The LLM does not create or modify the structured finding collection.

## 3.5 Reporting independence

Different reporting strategies consume the same deterministic `AssessmentAnalysis`.

## 3.6 Execution metadata integrity

Execution metadata describes provenance and timing. It does not participate in assessment-status calculation.

---

# 4. Input Validation Testing

`CreditPositionValidator` has dedicated unit tests covering both accepted and rejected inputs.

The test suite verifies that:

| Input condition | Expected behavior |
|---|---|
| Valid `CreditPosition` | Accepted |
| Blank/whitespace `position_id` | Rejected with `ValueError` |
| Non-numeric financial field | Rejected with `ValueError` |
| Boolean in numeric field | Rejected with `ValueError` |
| `NaN` | Rejected with `ValueError` |
| Positive/negative infinity | Rejected with `ValueError` |
| Wrong object type | Rejected with `TypeError` |
| `None` financial value | Accepted for downstream rule handling |

The validation is structural rather than a credit-policy validator. For example, negative financial values are not rejected generically because their interpretation depends on the business rule evaluating the specific indicator.

The `AssessmentService` injects the validator and invokes it before the Rule Engine. This makes the validation boundary explicit and independently testable.

---

# 5. Unit and Rule Testing

Unit tests cover:

- domain models;
- input validation;
- rule status and severity types;
- severity policy;
- configuration loading and validation;
- rule registration and discovery;
- individual financial rules;
- Rule Engine behavior;
- assessment service and status calculation;
- analysis agent;
- deterministic report generation;
- LLM report generation;
- LLM clients and mock client;
- reporting agent and error classification;
- workflow and orchestration;
- execution metadata.

For deterministic rules, the core property is:

```text
Same Input
    +
Same Configuration
    ↓
Same RuleResult
```

Tests cover normal evaluations, triggered conditions, threshold boundaries and non-evaluable inputs where applicable.

---

# 6. Rule Validation

Each rule returns a structured `RuleResult` containing information such as:

- rule identifier and name;
- category;
- status;
- evaluated value;
- threshold;
- severity;
- reason.

The three rule outcomes are:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

The explicit `NOT_EVALUABLE` state prevents missing or unsuitable data from being silently interpreted as a negative credit signal.

### Severity

Directional severity policies include:

```text
LOWER_IS_WORSE
HIGHER_IS_WORSE
```

Tests verify trigger thresholds and graduated severity thresholds independently.

### Configuration

The YAML configuration is validated for required fields, unique rule IDs, supported severity values/directions and valid threshold definitions.

---

# 7. Assessment and Status Validation

The deterministic assessment sequence is:

```text
CreditPosition
      ↓
CreditPositionValidator
      ↓
RuleEngine
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

Validation verifies that rule results, findings and the position identifier are preserved and that the overall status is calculated from deterministic rule results.

The current status rules are:

| Rule-result condition | Assessment status |
|---|---|
| 2+ `TRIGGERED` | `CRITICAL` |
| Exactly 1 `TRIGGERED` | `ATTENTION` |
| 0 triggered + at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

The all-`NOT_EVALUABLE` test is important because **no triggered rule is not necessarily equivalent to normal credit quality** when no indicator could actually be evaluated.

The analysis stage is validated to ensure:

```text
Assessment.status
        =
AssessmentAnalysis.assessment_status
```

The analysis layer organizes evidence but does not perform a second credit assessment.

---

# 8. Reporting Validation

## 8.1 Deterministic reporting

`DeterministicReportGenerator` must produce a report without external LLM dependencies while preserving the structured assessment information.

## 8.2 LLM reporting

`LLMReportGenerator` consumes `AssessmentAnalysis`, builds a constrained prompt and delegates text generation to an injected `LLMClient`.

The generated narrative is not the source of truth for assessment status.

---

# 9. LLM Narrative Contract

The prompt contract is tested explicitly. It requires the LLM to:

- represent all supplied material findings;
- preserve supplied numerical values and units;
- avoid rounding, recalculation or conversion;
- avoid unsupported facts and causal explanations;
- avoid inferring sales volume, pricing, demand, costs, liquidity, cash flow, debt service capacity or financial stability unless supplied;
- preserve category order;
- discuss each category at most once;
- avoid category headings and list-like output;
- mention each material indicator value once;
- avoid repeated indicators, findings and conclusions;
- end after the final material finding;
- not generate the assessment status.

The dedicated prompt tests assert the presence of these contractual instructions, including category ordering and non-repetition requirements.

---

# 10. Indicator Grounding Validation

The current implementation supports strict indicator grounding for LLM reporting.

When `require_indicator_values=True`, deterministic indicator values extracted from the supplied findings are required to appear in the generated narrative.

Conceptually:

```text
Deterministic findings
        ↓
Extract required indicators
        ↓
LLM narrative
        ↓
Grounding validation
     /       \\
   valid    invalid
     ↓         ↓
  Narrative  Deterministic fallback
```

Validation tests cover:

- all required indicator values present;
- a missing indicator triggering deterministic fallback;
- no unnecessary fallback when all required values are present;
- duplicate indicator values not being silently rewritten;
- strict grounding being configurable;
- Ollama workflow configuration enabling indicator grounding.

The grounding check is intentionally narrow. It protects required numerical evidence but is not a full semantic fact-checker.

---

# 11. Deterministic Status Protection

The final structured assessment status is application-controlled.

For an AI-assisted report, the status is constructed from deterministic assessment data and displayed separately from the generated narrative.

Tests verify that the status is preserved exactly and that generated narrative cannot replace the structured status.

---

# 12. LLM Response Validation Boundary

The implementation deliberately avoids broad semantic string-matching rules that would attempt to decide whether an arbitrary narrative is "correct".

The validation boundary is split into:

1. **Structural input validation** — malformed positions are rejected before assessment.
2. **Deterministic structured status protection** — status is owned by application logic.
3. **Prompt contract** — the model receives explicit grounding and narrative constraints.
4. **Optional indicator grounding validation** — required deterministic numerical evidence must be present when strict mode is enabled.
5. **Fallback** — a failed grounding check produces a deterministic report.

This provides a controlled compromise between safety, testability and natural-language flexibility.

---

# 13. Fallback and Resilience Validation

The reporting agent supports a primary generator and deterministic fallback.

Tests cover:

- LLM client errors;
- empty/invalid generated responses;
- provider exceptions;
- error classification;
- successful deterministic fallback;
- fallback failure;
- terminal propagation when both generators fail;
- strict grounding failure and deterministic fallback.

Operational error categories include:

```text
RATE_LIMIT
SERVICE_UNAVAILABLE
CONNECTION_ERROR
AUTHENTICATION
AUTHORIZATION
MODEL_UNAVAILABLE
TIMEOUT
GENERATION_ERROR
```

The key resilience property is:

> **Failure of the optional LLM reporting path must not invalidate the deterministic assessment.**

---

# 14. LLM Provider Abstraction

LLM access is abstracted behind `LLMClient` with provider-specific implementations such as Gemini and Ollama and a mock implementation for tests.

```text
                 LLMClient
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Gemini      Ollama       Mock
```

---

# 15. Workflow and Orchestration Validation

The complete workflow is:

```text
CreditPosition
      ↓
Validation
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

Workflow tests verify correct dependency construction and propagation of data through the complete processing chain.

The principal end-to-end invariant is:

```text
Assessment.status
      =
AssessmentAnalysis.assessment_status
      =
Report.assessment_status
```

Terminal reporting failure is also tested: if both primary and fallback generators fail, the error is propagated rather than silently converted into success.

---

# 16. Execution Metadata Validation

`ExecutionMetadata` is immutable provenance for successful workflow executions.

Tests verify:

- unique execution ID;
- timezone-aware UTC timestamp;
- selected reporting mode;
- primary/fallback generator state;
- correct `fallback_used` state;
- primary reporting error category when fallback occurs;
- non-negative phase timings;
- total execution timing consistency.

The metadata is diagnostic information and does not participate in assessment-status calculation.

---

# 17. Presentation Validation Boundary

The Streamlit UI is intentionally downstream of the decision engine.

The current Results view is validated as a presentation hierarchy:

```text
Executive Credit Assessment
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The presentation layer consumes structured workflow objects and renders:

- Executive Credit Assessment;
- graphical Decision Path;
- rule-outcome distribution;
- severity profile;
- filterable Rule Catalogue;
- individual rule detail with indicator, actual value, configured threshold, status, severity, direction and rationale;
- credit data;
- methodology;
- execution metadata.

The Risk Indicator Dashboard is the single detailed rule-evidence surface. The Audit Trail contains broader workflow and traceability information.

All visualizations are presentation-only: the UI does not recalculate thresholds, severity or assessment status.

---

# 18. CI Quality Gates

The GitHub Actions workflow runs on Python **3.13 and 3.14** and enforces:

```text
Install dependencies
        ↓
Ruff linting
        ↓
Mypy type checking
        ↓
Pytest + coverage
```

The pytest command enforces a minimum coverage of **95% for `src`**.

The current CI workflow is configured for pushes to `main` and pull requests targeting `main`.

The latest validation changes are therefore intended to be protected by the same automated quality gates as the rest of the deterministic core.

---

# 19. Validation Matrix

| Area | Validation mechanism | Expected property |
|---|---|---|
| Input validation | Validator unit tests | Invalid structural input is rejected before assessment |
| Rule evaluation | Unit tests | Deterministic `RuleResult` |
| Thresholds | Rule tests | Configured thresholds are applied correctly |
| Severity | Severity-policy tests | Direction and thresholds are respected |
| Non-evaluable inputs | Rule/service/status tests | `NOT_EVALUABLE` is handled explicitly |
| Configuration | Config tests | Invalid configuration is rejected |
| Rule registry | Registry tests | Correct implementation is discovered |
| Assessment service | Unit/integration tests | Results, findings and status are composed correctly |
| Analysis | Agent tests | Deterministic status and findings remain authoritative |
| Deterministic reporting | Generator tests | Report works without an external LLM |
| Prompt contract | Prompt tests | Grounding and narrative constraints remain explicit |
| Indicator grounding | LLM generator tests | Required values are preserved or fallback occurs |
| LLM reporting | Generator/client tests | Narrative is generated from controlled analysis data |
| Error classification | Reporting-agent tests | Provider failures map to stable categories |
| Fallback | Reporting-agent tests | Primary failure can fall back deterministically |
| Terminal failure | Reporting/workflow tests | Fallback failure is propagated |
| Workflow propagation | Workflow/integration tests | Assessment status remains unchanged across layers |
| Execution metadata | Workflow tests | Provenance and timings are consistent |
| Presentation boundary | UI architecture review | UI remains read-only and does not reproduce decision logic |
| CI | GitHub Actions | Ruff, Mypy and pytest/coverage pass on supported Python versions |

---

# 20. Testing Philosophy

The project uses tests not only to verify implementation details but also to protect architectural boundaries.

The most important contracts are therefore:

```text
Valid structural input → deterministic assessment

Deterministic rules → deterministic assessment

Deterministic assessment → controlled analysis

Controlled analysis → bounded reporting

LLM failure / invalid grounding → deterministic fallback

Presentation → read-only consumer of decision evidence
```

This keeps the test suite aligned with the core credit-risk design rather than treating the UI or LLM output as an independent source of truth.
