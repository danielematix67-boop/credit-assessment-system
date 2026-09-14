# System Validation

## 1. Purpose

The validation strategy verifies functional correctness, architectural integrity and resilience of the `credit-assessment-system`.

The assessment layer is deterministic; AI is optional and limited to reporting. The central invariant is:

> **The deterministic assessment is the source of truth. The LLM can generate narrative content, but it cannot determine, modify or override the structured credit assessment.**

Validation therefore covers input integrity, configuration, all four assessment domains, final aggregation, analysis, reporting, LLM grounding, fallback behaviour, workflow propagation, execution metadata, scenario coverage and CI quality gates.

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
| Unit | Components, validators, rules and policies |
| Integration | Interactions between application layers |
| Workflow | Assessment-to-report propagation |
| LLM / grounding | Narrative constraints and evidence preservation |
| Scenario | End-to-end demonstration of configured domains/rules |
| CI | Repeatable lint, type and coverage gates |

---

## 3. Core Architectural Invariants

### 3.1 Deterministic decision authority

```text
CreditPosition + Case Inputs
          ↓
Domain Assessment Services
          ↓
Assessment Sections
          ↓
FinalAssessmentService
          ↓
Final Assessment
```

The LLM is not part of this decision path.

### 3.2 Input validation precedes assessment

`CreditPositionValidator` rejects malformed structural input, including wrong object types, blank identifiers, non-numeric values, booleans used as numbers and non-finite values. `None` remains valid for explicit `NOT_EVALUABLE` handling.

### 3.3 Deterministic status propagation

The case layer consolidates four domain statuses into the deterministic final assessment. Reporting receives that structured result; it does not recreate the decision.

### 3.4 Structured finding integrity

```text
RuleResult / Domain Evidence
          ↓
AssessmentSection
          ↓
Deterministic Analysis
          ↓
Report
```

The LLM does not create or modify the structured finding collection.

### 3.5 Execution metadata integrity

Execution metadata describes provenance and timing. It does not participate in assessment-status calculation.

---

## 4. Rule and Configuration Testing

The current configured inventory contains **17 rules**:

| Domain | Rule IDs | Count |
|---|---|---:|
| Customer Profile | `CP001–CP003` | 3 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Tests cover:

- rule status and severity types;
- severity direction and thresholds;
- YAML configuration loading and validation;
- rule registration/discovery;
- financial rules R001–R007;
- behavioural rules B001–B004;
- debt-sustainability rules DS001–DS003;
- customer-profile rules CP001–CP003;
- threshold boundaries;
- missing/non-evaluable inputs.

For deterministic rules:

```text
Same Input + Same Configuration
              ↓
        Same RuleResult
```

---

## 5. Assessment and Status Validation

For rule-based sections:

| Rule-result condition | Assessment status |
|---|---|
| 2+ `TRIGGERED` | `CRITICAL` |
| Exactly 1 `TRIGGERED` | `ATTENTION` |
| 0 triggered + at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

For the case:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 ATTENTION section        → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward that threshold, while `CRITICAL` can still produce a `CRITICAL` final assessment.

---

## 6. End-to-End Scenario Coverage

The predefined synthetic scenario is expected to exercise all four assessment domains and provide the inputs required by the configured rule inventory.

The target coverage contract is:

```text
4 assessment domains
        +
17 configured rule IDs
        +
NORMAL / ATTENTION / CRITICAL outcomes
        ↓
End-to-end Streamlit demonstration
```

Scenario data is synthetic/anonymized and must not contain production banking information.

Scenario coverage is a demonstration concern and does not replace the unit/integration tests that validate individual rule semantics.

---

## 7. Analysis and Reporting Validation

The reporting contract is:

```text
Deterministic Assessment
          ↓
Deterministic Analysis
          ↓
Reporting Agent
          ↓
Deterministic or Optional LLM Generator
          ↓
Report
```

Different generators consume the same deterministic analysis data. The generated narrative is never the source of truth for assessment status.

The Executive Narrative must preserve the application-controlled order:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

The model supplies prose only; Python controls titles and structure.

---

## 8. LLM Narrative Contract

The reporting prompt requires the LLM to:

- represent supplied material findings;
- preserve supplied numerical evidence and units;
- avoid unsupported facts and causal explanations;
- avoid recalculating supplied indicators;
- preserve the canonical category order;
- avoid generating the assessment status;
- avoid repeated indicators, findings and conclusions.

The deterministic assessment remains outside the generated narrative.

---

## 9. Indicator Grounding Validation

When `require_indicator_values=True`, required deterministic indicator values must appear in the generated narrative.

```text
Deterministic findings
        ↓
Required indicators
        ↓
LLM narrative
        ↓
Grounding validation
     /       \
   valid    invalid
     ↓         ↓
 Narrative  Deterministic fallback
```

Tests cover required-value presence, missing-value fallback, strict-mode configuration and duplicate-value handling.

The grounding check is intentionally narrow: it protects required numerical evidence but is not a full semantic fact-checker.

---

## 10. LLM Resilience Validation

The reporting agent supports a primary generator and deterministic fallback.

Tests cover:

- provider exceptions;
- empty/invalid generated responses;
- error classification;
- successful deterministic fallback;
- strict grounding failure and fallback;
- fallback failure;
- terminal propagation when both generators fail.

The key property is:

> **Failure of the optional LLM reporting path must not invalidate the deterministic assessment.**

---

## 11. Workflow Validation

The workflow preserves deterministic assessment data across layers:

```text
Input
 ↓
Validation
 ↓
Domain assessments
 ↓
CreditAssessmentCase
 ↓
Final Assessment
 ↓
Deterministic Analysis
 ↓
Reporting
```

The principal invariant is that reporting cannot modify the case-level decision or structured evidence.

---

## 12. Execution Metadata Validation

`ExecutionMetadata` is immutable provenance for workflow executions.

Tests verify execution identity, timezone-aware UTC timestamp, reporting mode, generator/fallback state, error category when applicable, non-negative phase timings and total timing consistency.

Metadata is diagnostic information and does not participate in assessment-status calculation.

---

## 13. Presentation Validation Boundary

The current Streamlit Results hierarchy is:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
          ↓
Risk Drivers (collapsed)
          ↓
Detailed Assessment (collapsed)
          ↓
Rule Catalogue & Filters (collapsed)
          ↓
Individual Rule Detail (collapsed)
```

The presentation layer consumes structured workflow objects and renders progressively deeper evidence:

- **Executive Credit Assessment** — final status and compact KPIs;
- **Assessment by Macro-Area** — authoritative four-domain overview;
- **Executive Narrative** — management-level prose from deterministic evidence;
- **Risk Drivers** — triggered evidence ranked by severity;
- **Detailed Assessment** — analyst/audit drill-down and data quality;
- **Rule Catalogue / Detail** — technical inspection on demand.

The UI does not recalculate thresholds, severity or assessment status. Aggregate views that duplicated the macro-area evidence were removed.

---

## 14. CI Quality Gates

GitHub Actions runs on Python **3.13 and 3.14** and enforces:

```text
Install dependencies
        ↓
Ruff linting
        ↓
Mypy type checking
        ↓
Pytest + coverage
```

The pytest command enforces minimum coverage of **95% for `src`**.

---

## 15. Validation Matrix

| Area | Validation mechanism | Expected property |
|---|---|---|
| Input validation | Validator tests | Invalid structural input rejected before assessment |
| Rule evaluation | Unit tests | Deterministic `RuleResult` |
| Thresholds | Rule tests | Configured thresholds applied correctly |
| Severity | Severity-policy tests | Direction and thresholds respected |
| Non-evaluable inputs | Rule/service/status tests | `NOT_EVALUABLE` handled explicitly |
| Configuration | Config tests | Invalid configuration rejected |
| Rule registry | Registry tests | Correct implementation discovered |
| Domain assessment | Unit/integration tests | Domain evidence and status composed correctly |
| Case aggregation | Case/service tests | Four domain statuses produce deterministic final assessment |
| Scenario coverage | Scenario/integration tests | Domains and configured rule inventory exercised |
| Analysis | Agent tests | Deterministic findings remain authoritative |
| Deterministic reporting | Generator tests | Report works without external LLM |
| Prompt contract | Prompt tests | Narrative constraints remain explicit |
| Indicator grounding | LLM generator tests | Required values preserved or fallback occurs |
| LLM reporting | Generator/client tests | Narrative uses controlled analysis data |
| Error classification | Reporting-agent tests | Provider failures map to stable categories |
| Fallback | Reporting-agent tests | Primary failure can fall back deterministically |
| Terminal failure | Reporting/workflow tests | Fallback failure is propagated |
| Workflow propagation | Integration tests | Deterministic assessment remains unchanged |
| Execution metadata | Workflow tests | Provenance and timings are consistent |
| Presentation boundary | UI architecture tests/review | UI remains read-only |
| CI | GitHub Actions | Ruff, Mypy and pytest/coverage pass on supported Python versions |

---

## 16. Testing Philosophy

Tests protect both implementation behaviour and architectural boundaries.

```text
Valid structural input → deterministic assessment

Deterministic rules → deterministic domain evidence

Domain evidence → deterministic final assessment

Deterministic assessment → controlled analysis

Controlled analysis → bounded reporting

LLM failure / invalid grounding → deterministic fallback

Presentation → read-only consumer of decision evidence
```

This keeps validation aligned with the project's credit-risk design rather than treating the UI or LLM output as an independent source of truth.
