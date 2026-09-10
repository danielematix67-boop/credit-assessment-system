# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment application with an optional AI-assisted reporting layer.

The architecture now distinguishes two levels:

1. **Deterministic financial assessment** — evaluates the existing indicator/rule catalogue.
2. **Credit analysis case** — organizes the assessment into the macro-areas followed by a credit analyst: customer profile, financial analysis, behavioural analysis and debt sustainability.

The central boundary remains:

> **Deterministic evidence is the source of truth. The LLM is an optional reporting component and has no decision authority.**

The repository keeps framework-independent logic under `src/` and the Streamlit presentation layer under `app/`.

---

## 2. Architectural Principles

| Principle | Implementation |
|---|---|
| Structural input validation | `CreditPositionValidator` rejects malformed positions before rule evaluation. |
| Deterministic decision authority | Rule results and assessment status are calculated without an LLM. |
| Macro-area separation | `CreditAssessmentCase` separates customer profile, financial, behavioural and debt-sustainability analysis. |
| Financial dimension grouping | Existing rules are organized into analyst-oriented financial dimensions without duplicating rule logic. |
| Explicit non-evaluability | Unimplemented or unavailable macro-areas are represented as `NOT_EVALUABLE`, not silently treated as normal. |
| Separation of concerns | Validation, assessment, case composition, analysis and reporting are separate responsibilities. |
| Configuration-driven rules | Thresholds and severity parameters are externalized in `config/rules.yaml`. |
| Provider independence | Gemini and Ollama are accessed through the `LLMClient` abstraction. |
| Graceful degradation | LLM reporting can fall back to deterministic reporting. |
| Grounded narrative generation | LLM prompts and optional response validation constrain narrative output to supplied evidence. |
| Execution observability | Provenance, fallback state, error classification and timings are exposed separately from decision data. |
| UI/domain decoupling | Streamlit presentation code does not own credit-risk business rules. |

---

## 3. System Architecture

```text
CreditPosition
      │
      ▼
CreditPositionValidator
      │
      ▼
AssessmentService
      │
      ├── RuleEngine → RuleResult[]
      ├── CommentEngine → RuleFinding[]
      └── StatusCalculator → Assessment
                                  │
                                  ▼
                    CreditAssessmentCaseService
                                  │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
 Customer Profile       Financial Analysis      Behavioural Analysis
 NOT_EVALUABLE              evaluated             NOT_EVALUABLE
                                  │
                                  ▼
                         Debt Sustainability
                           NOT_EVALUABLE
                                  │
                                  ▼
                       Future Case Aggregator
                                  │
                                  ▼
                           Analysis / LLM
                                  │
                                  ▼
                              Report
```

**Current status:** the financial-analysis section is backed by the existing deterministic rule engine and is now organized into analyst-oriented dimensions. Customer profile, behavioural analysis and debt sustainability remain explicit `NOT_EVALUABLE` placeholders. A final cross-section aggregator is intentionally deferred until additional macro-areas have deterministic logic.

The existing `AssessmentWorkflow` remains compatible with the current financial assessment/reporting path. `CreditAssessmentCaseService` is an additive domain layer for the thesis evolution.

### Dependency direction

```text
Streamlit (`app/`)
       ↓
Application / Orchestration
       ↓
Services / Agents
       ↓
Rules / Domain Models
```

The core library does not depend on Streamlit.

---

## 4. Credit Analysis Case Layer

`CreditAssessmentCase` is the higher-level domain representation of a complete credit-analysis process.

```text
CreditAssessmentCase
│
├── Customer Profile
├── Financial Analysis
├── Behavioural Analysis
└── Debt Sustainability
```

Each macro-area is represented by an `AssessmentSection` containing:

- section name;
- deterministic status;
- findings;
- evidence;
- limitations;
- optional analyst-oriented dimensions.

`SectionStatus` supports:

```text
NORMAL
ATTENTION
CRITICAL
NOT_EVALUABLE
```

This is deliberately distinct from the existing `AssessmentStatus`: the latter remains the status of the current deterministic financial assessment, while `SectionStatus` can represent a macro-area that has not yet been implemented or cannot be evaluated.

The sections are ordered according to the intended analyst reasoning flow:

```text
1. Customer Profile
        ↓
2. Financial Analysis
        ↓
3. Behavioural Analysis
        ↓
4. Debt Sustainability
        ↓
5. Final Judgement
```

The final judgement/aggregation policy is not implemented yet. This prevents the system from producing a misleading overall decision while most macro-areas are still unavailable.

### Financial Analysis dimensions

The seven existing deterministic rules are grouped without changing their evaluation logic:

```text
Financial Analysis
│
├── Revenue & Growth
│   └── R001 Revenue growth deterioration
│
├── Profitability
│   ├── R002 Negative EBITDA
│   └── R003 EBITDA margin deterioration
│
├── Financial Structure
│   └── R004 NFP / EBITDA leverage
│
├── Debt Service Burden
│   ├── R005 Interest expense / EBITDA
│   └── R007 Interest coverage ratio
│
└── Profitability Quality
    └── R006 EBITDA materially supported by finished goods inventory increase
```

These dimensions are an organizational layer over `RuleResult[]`. The deterministic rules remain the single source of truth and are not duplicated inside the case model.

### Phase 1 mapping

The current seven deterministic rules remain the foundation of `Financial Analysis`:

```text
Existing AssessmentService
          ↓
RuleResult[]
          ↓
Financial dimension mapping
          ↓
Financial Analysis section
          ↓
CreditAssessmentCase
```

This preserves backward compatibility while establishing a stable extension point for behavioural and debt-sustainability modules.

---

## 5. Input Validation Layer

`CreditPositionValidator` performs structural validation before deterministic assessment begins.

The validator checks:

- the object is a `CreditPosition`;
- `position_id` is non-empty;
- numeric financial fields contain numeric values or `None`;
- boolean values are not accepted as numeric inputs;
- numeric values are finite, rejecting `NaN` and positive/negative infinity.

`None` is intentionally accepted because unavailable financial information is a valid domain condition and can subsequently produce `NOT_EVALUABLE` rule outcomes.

The validator does not impose business-specific sign constraints. Whether a negative value is economically meaningful remains the responsibility of the corresponding deterministic rule.

---

## 6. Assessment Layer

`AssessmentService` owns the deterministic financial assessment stage:

```text
CreditPosition
      ↓
CreditPositionValidator
      ↓
RuleEngine.evaluate()
      ↓
RuleResult[]
      ↓
CommentEngine
      ↓
RuleFinding[]
      ↓
AssessmentStatusCalculator
      ↓
Assessment
```

No LLM is involved in this path.

### Status calculation

The current status logic is:

| Rule outcome condition | Assessment |
|---|---|
| 2+ `TRIGGERED` | `CRITICAL` |
| Exactly 1 `TRIGGERED` | `ATTENTION` |
| 0 triggered and at least one evaluable rule | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

The all-`NOT_EVALUABLE` case is intentionally conservative: the absence of evaluable evidence is not treated as equivalent to a normal assessment.

---

## 7. Rule Engine

Rules implement a common abstraction and are resolved through the rule registry.

```text
Rule.evaluate(position) → RuleResult
```

The current configured rule catalogue contains revenue, profitability, leverage and interest-coverage indicators.

Each rule can produce:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

`NOT_EVALUABLE` is used when a rule cannot safely assess its indicator because the required domain data is unavailable or unsuitable. This state is distinct from `NOT_TRIGGERED`.

Rule parameters are externalized in `config/rules.yaml`.

---

## 8. Analysis and Reporting Layers

The existing downstream path remains:

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

The intended evolution is to feed the higher-level case into analysis only after its deterministic sections are available:

```text
CreditAssessmentCase
        ↓
Deterministic section evidence
        ↓
Final cross-section aggregation
        ↓
Analysis / Executive Synthesis
        ↓
Report
```

The LLM remains responsible only for natural-language synthesis. It must not infer a status from raw data or override deterministic findings.

---

## 9. Presentation Layer — `app/`

The Streamlit application is responsible for input collection, reporting-mode selection, workflow execution and presentation of domain results.

The current Results view is organized from executive outcome toward evidence:

```text
Executive Credit Assessment
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The Risk Indicator Dashboard consumes deterministic `RuleResult` fields directly and does not duplicate rule calculations.

---

## 10. Repository Structure

```text
credit-assessment-system/
├── app/                         # Streamlit presentation layer
├── config/
│   └── rules.yaml
├── src/
│   ├── agents/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   │   ├── assessment.py
│   │   ├── assessment_section.py
│   │   ├── assessment_status.py
│   │   ├── credit_assessment_case.py
│   │   └── position.py
│   ├── orchestration/
│   ├── rules/
│   └── services/
│       ├── assessment_service.py
│       ├── assessment_status_calculator.py
│       ├── credit_assessment_case_service.py
│       └── position_validator.py
├── docs/
└── tests/
```

---

## 11. Extension Roadmap

The case layer is intentionally incremental:

### Phase 1 — Case structure

Completed. Introduce the macro-area contract while keeping only financial analysis evaluable.

### Phase 2 — Financial Analysis formalization

Completed. Existing rules are grouped into analyst-oriented financial dimensions without duplicating or changing deterministic rule logic.

### Phase 3 — Behavioural Analysis

Introduce synthetic banking-behaviour inputs and deterministic indicators such as utilization, overdrafts, past-due positions, payment delays and exposure trends.

### Phase 4 — Debt Sustainability

Introduce deterministic cash-flow and debt-service indicators, including DSCR and related repayment-capacity measures.

### Phase 5 — Customer Profile

Introduce structured company/relationship information, historical facilities and early-warning information.

### Phase 6 — Final Aggregation

Define and test an explicit cross-section aggregation policy. No implicit averaging should be used; criticality rules must be documented and deterministic.

### Phase 7 — Executive Synthesis

Adapt the reporting layer so the LLM receives section-level deterministic evidence and produces a coherent analyst-style executive narrative.

---

## 12. Architectural Boundary

```text
                  DETERMINISTIC CORE
                         │
                         ▼
                Input Validation
                         │
                         ▼
                  Financial Rules
                         │
                         ▼
                 Macro-area Evidence
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Deterministic            LLM-assisted
       decision logic             synthesis
              │                     │
              └──────────┬──────────┘
                         ▼
                    Executive
                      Report
```

The LLM is an optional, replaceable and bounded synthesis dependency rather than part of the credit decision itself.
