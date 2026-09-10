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
| Unit | Validate components, input validation and business rules |
| Integration | Validate interactions between application layers |
| Workflow | Validate the assessment-to-report pipeline |
| LLM / grounding | Validate narrative constraints and evidence preservation |
| CI | Enforce repeatable lint, type and coverage gates |

---

## 3. Core Architectural Invariants

### 3.1 Deterministic decision authority

```text
CreditPosition
      ↓
Rule Engine / Case Services
      ↓
Rule Results / Section Statuses
      ↓
Final Assessment
```

The LLM is not part of this decision path.

### 3.2 Input validation precedes assessment

```text
CreditPosition
      ↓
CreditPositionValidator
   /             \\
valid           invalid
  ↓                 ↓
Rule Engine      Reject input
```

Structural validation rejects malformed positions, non-numeric values, booleans used as numbers and non-finite values. `None` is accepted so rules can explicitly return `NOT_EVALUABLE`.

The validator does not impose generic business sign constraints; those remain the responsibility of the relevant credit rule.

### 3.3 Deterministic status propagation

The financial status is preserved through the reporting workflow:

```text
Assessment.status
       ↓
AssessmentAnalysis.assessment_status
       ↓
Report.assessment_status
```

The case layer additionally consolidates macro-area statuses through `FinalAssessmentService`.

### 3.4 Structured finding integrity

```text
RuleResult
    ↓
RuleFinding
    ↓
Assessment / AssessmentSection
    ↓
AssessmentAnalysis
    ↓
Report
```

The LLM does not create or modify the structured finding collection.

### 3.5 Execution metadata integrity

Execution metadata describes provenance and timing. It does not participate in assessment-status calculation.

---

## 4. Input Validation Testing

`CreditPositionValidator` is independently tested for accepted and rejected inputs.

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

`AssessmentService` invokes validation before Rule Engine evaluation, creating an explicit and testable decision boundary.

---

## 5. Rule and Configuration Testing

Unit tests cover:

- rule status and severity types;
- severity policies and directionality;
- YAML configuration loading and validation;
- rule registration and discovery;
- individual financial rules R001–R007;
- behavioural indicators B001–B004;
- debt-sustainability indicators DS001–DS003;
- customer-profile flags CP001–CP002;
- threshold boundaries;
- missing/non-evaluable inputs.

For deterministic rules:

```text
Same Input + Same Configuration
              ↓
        Same RuleResult
```

Each `RuleResult` exposes structured evidence including identifier, category, status, value, threshold, severity and reason.

---

## 6. Assessment and Status Validation

The financial assessment sequence is:

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

The financial status rules are:

| Rule-result condition | Assessment status |
|---|---|
| 2+ `TRIGGERED` | `CRITICAL` |
| Exactly 1 `TRIGGERED` | `ATTENTION` |
| 0 triggered + at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

The explicit all-`NOT_EVALUABLE` case protects the distinction between **no detected risk signal** and **insufficient evaluable evidence**.

### Final case aggregation

`FinalAssessmentService` applies:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 ATTENTION section        → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward that two-area threshold, while `CRITICAL` can still produce a `CRITICAL` final assessment.

Tests verify deterministic propagation and preservation of status across the workflow.

---

## 7. Analysis and Reporting Validation

The financial reporting contract is:

```text
Assessment
    ↓
AnalysisAgent
    ↓
AssessmentAnalysis
    ↓
ReportingAgent
    ↓
Report
```

Different report generators consume the same deterministic analysis data. The generated narrative is never the source of truth for assessment status.

The case pipeline separately exposes deterministic macro-area evidence and `FinalAssessment` to the application/UI.

---

## 8. LLM Narrative Contract

The reporting prompt is tested as an explicit contract. It requires the LLM to:

- represent all supplied material findings;
- preserve supplied numerical values and units;
- avoid rounding, recalculation or conversion;
- avoid unsupported facts and causal explanations;
- avoid inferring sales volume, pricing, demand, costs, liquidity, cash flow, debt-service capacity or financial stability unless supplied;
- preserve category order;
- discuss each category at most once;
- avoid category headings and list-like output;
- mention each material indicator value once;
- avoid repeated indicators, findings and conclusions;
- not generate the assessment status.

---

## 9. Indicator Grounding Validation

When `require_indicator_values=True`, deterministic indicator values extracted from supplied findings must appear in the generated narrative.

```text
Deterministic findings
        ↓
Required indicators
        ↓
LLM narrative
        ↓
Grounding validation
     /       \\
   valid    invalid
     ↓         ↓
 Narrative  Deterministic fallback
```

Tests cover required-value presence, missing-value fallback, strict-mode configuration and duplicate-value handling.

The grounding check is intentionally narrow: it protects required numerical evidence but is not a full semantic fact-checker.

---

## 10. Deterministic Status Protection

For AI-assisted reports, the structured status is application-controlled and displayed separately from generated prose.

The key invariant is:

```text
Generated narrative ≠ assessment authority
```

A narrative cannot replace or override the deterministic status.

---

## 11. LLM Response and Resilience Validation

The reporting agent supports a primary generator and deterministic fallback.

Tests cover:

- provider exceptions;
- empty/invalid generated responses;
- error classification;
- successful deterministic fallback;
- strict grounding failure and fallback;
- fallback failure;
- terminal propagation when both generators fail.

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

## 12. Workflow and Orchestration Validation

The main financial workflow is:

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

The case workflow additionally builds macro-area sections and `FinalAssessment`.

The principal financial invariant is:

```text
Assessment.status
      =
AssessmentAnalysis.assessment_status
      =
Report.assessment_status
```

If both primary and fallback reporting generators fail, the error is propagated rather than silently converted into success.

---

## 13. Execution Metadata Validation

`ExecutionMetadata` is immutable provenance for successful workflow executions.

Tests verify execution identity, timezone-aware UTC timestamp, reporting mode, generator/fallback state, error category when applicable, non-negative phase timings and total timing consistency.

Metadata is diagnostic information and does not participate in assessment-status calculation.

---

## 14. Presentation Validation Boundary

The Streamlit UI is intentionally downstream of the deterministic assessment engine.

The current Results hierarchy is:

```text
Executive Credit Assessment
          ↓
Final Assessment
          ↓
Risk Drivers
          ↓
Rule Engine Evidence
          ↓
Executive Narrative
          ↓
Detailed Analysis by Macro-area
```

The presentation layer consumes structured workflow objects and renders progressively deeper evidence:

- **Executive Credit Assessment** — final status and compact KPIs;
- **Final Assessment** — deterministic macro-area consolidation and limitations;
- **Risk Drivers** — cross-area ranking of triggered indicators;
- **Rule Engine Evidence** — outcome/severity distributions, filterable catalogue and rule detail;
- **Executive Narrative** — generated management-level narrative;
- **Detailed Analysis by Macro-area** — deeper financial, behavioural, debt-sustainability and customer-profile evidence.

Technical tables and detailed drill-downs are closed by default where appropriate. This keeps the executive view concise while preserving auditability.

All visualizations are presentation-only: the UI does not recalculate thresholds, severity or assessment status.

---

## 15. CI Quality Gates

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

The workflow is configured for pushes to `main` and pull requests targeting `main`.

---

## 16. Validation Matrix

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
| Case aggregation | Case/service tests | Macro-area statuses produce deterministic final assessment |
| Analysis | Agent tests | Deterministic status and findings remain authoritative |
| Deterministic reporting | Generator tests | Report works without an external LLM |
| Prompt contract | Prompt tests | Grounding and narrative constraints remain explicit |
| Indicator grounding | LLM generator tests | Required values are preserved or fallback occurs |
| LLM reporting | Generator/client tests | Narrative uses controlled analysis data |
| Error classification | Reporting-agent tests | Provider failures map to stable categories |
| Fallback | Reporting-agent tests | Primary failure can fall back deterministically |
| Terminal failure | Reporting/workflow tests | Fallback failure is propagated |
| Workflow propagation | Workflow/integration tests | Assessment status remains unchanged across layers |
| Execution metadata | Workflow tests | Provenance and timings are consistent |
| Presentation boundary | UI architecture review | UI remains read-only and does not reproduce decision logic |
| CI | GitHub Actions | Ruff, Mypy and pytest/coverage pass on supported Python versions |

---

## 17. Testing Philosophy

Tests protect both implementation behavior and architectural boundaries.

The most important contracts are:

```text
Valid structural input → deterministic assessment

Deterministic rules → deterministic section evidence

Section evidence → deterministic final assessment

Deterministic assessment → controlled analysis

Controlled analysis → bounded reporting

LLM failure / invalid grounding → deterministic fallback

Presentation → read-only consumer of decision evidence
```

This keeps validation aligned with the project's credit-risk design rather than treating the UI or LLM output as an independent source of truth.
