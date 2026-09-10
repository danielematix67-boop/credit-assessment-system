# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment application with an optional AI-assisted reporting layer.

The architecture is organized around a higher-level `CreditAssessmentCase` that mirrors the main stages of an analyst-style credit analysis:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability
5. Final Assessment
6. Executive Synthesis

The central boundary remains:

> **Deterministic evidence is the source of truth. The LLM is an optional synthesis component and has no decision authority.**

Framework-independent logic lives under `src/`; Streamlit presentation remains under `app/`.

---

## 2. System Architecture

```text
CreditPosition
      │
      ▼
CreditAssessmentCaseService
      │
      ├── CustomerProfileAssessmentService
      ├── AssessmentService
      │      └── RuleEngine / CommentEngine / StatusCalculator
      ├── BehaviouralAssessmentService
      ├── DebtSustainabilityAssessmentService
      │
      ▼
CreditAssessmentCase
      │
      ▼
FinalAssessmentService
      │
      ▼
FinalAssessment
      │
      ▼
Case-level analysis / executive synthesis
      │
      ▼
Report
```

The existing `AssessmentService` remains the deterministic financial assessment engine. The case layer composes it with additional deterministic macro-area services.

### Dependency direction

```text
Streamlit (`app/`)
       ↓
Application / orchestration
       ↓
Services / agents
       ↓
Rules / domain models
```

The core domain does not depend on Streamlit.

---

## 3. Credit Assessment Case

`CreditAssessmentCase` is the domain container for the complete analyst-style assessment.

```text
CreditAssessmentCase
│
├── Customer Profile
├── Financial Analysis
├── Behavioural Analysis
├── Debt Sustainability
└── Final Assessment
```

Each macro-area is represented by `AssessmentSection` with deterministic status, findings, evidence, limitations and optional analyst-oriented dimensions.

`SectionStatus` supports `NORMAL`, `ATTENTION`, `CRITICAL` and `NOT_EVALUABLE`.

`NOT_EVALUABLE` explicitly represents missing or insufficient evidence. It is not silently converted into `NORMAL`.

---

## 4. Customer Profile

`CustomerProfileData` contains descriptive information normally collected during the initial customer presentation, including company name and legal form, sector, size class, geography, shareholders, management, relationship duration, historical facilities, active EWS/EWI signal and previous restructuring.

`CustomerProfileAssessmentService` evaluates explicit risk flags deterministically:

```text
CP001 — Active EWS
CP002 — Previous Restructuring
```

The profile section does not manufacture a risk judgement when no profile data are available; it returns `NOT_EVALUABLE`.

---

## 5. Financial Analysis

The seven existing deterministic rules remain the foundation of the financial section:

```text
Financial Analysis
│
├── Revenue & Growth
│   └── R001 Revenue growth deterioration
├── Profitability
│   ├── R002 Negative EBITDA
│   └── R003 EBITDA margin deterioration
├── Financial Structure
│   └── R004 NFP / EBITDA leverage
├── Debt Service Burden
│   ├── R005 Interest expense / EBITDA
│   └── R007 Interest coverage ratio
└── Profitability Quality
    └── R006 EBITDA materially supported by finished goods inventory increase
```

The case layer only groups the existing `RuleResult[]`; it does not duplicate their evaluation logic.

---

## 6. Behavioural Analysis

`BehaviouralData` provides synthetic banking-behaviour inputs. The deterministic service evaluates B001–B004 for credit utilization, overdraft duration, payment delays and exposure growth.

This layer is intentionally independent from the financial rules: behavioural data cannot modify the financial assessment.

---

## 7. Debt Sustainability

`DebtSustainabilityData` provides cash-flow and debt-service inputs. The deterministic service evaluates:

```text
DS001 — Debt Service Coverage Ratio
        CFADS / Debt Service

DS002 — Debt Service / EBITDA
        Debt Service / EBITDA

DS003 — Cash Flow Debt-Service Buffer
        CFADS − Debt Service
```

The implementation deliberately avoids duplicating the existing financial indicators R004, R005 and R007. The section uses the same deterministic status policy as the other rule-based sections.

---

## 8. Final Aggregation

`FinalAssessmentService` combines section-level statuses using an explicit deterministic policy:

```text
Any CRITICAL section → CRITICAL
2+ ATTENTION sections → CRITICAL
1 ATTENTION section  → ATTENTION
All evaluable sections NORMAL → NORMAL
No evaluable sections → ATTENTION
```

`NOT_EVALUABLE` sections are excluded from the positive/negative count but are reported as limitations. No averaging, weighted score or LLM judgement is used.

---

## 9. Validation and Deterministic Decision Boundary

`CreditPositionValidator` performs structural validation before financial rule evaluation. It rejects malformed positions, non-numeric values, booleans used as numbers, `NaN` and infinities while allowing `None` for unavailable information.

The financial assessment flow is:

```text
CreditPosition → CreditPositionValidator → RuleEngine → RuleResult[]
              → CommentEngine → RuleFinding[] → StatusCalculator → Assessment
```

No LLM participates in this decision path.

---

## 10. Analysis and Reporting Boundary

The existing reporting path remains compatible with the original financial assessment:

```text
Assessment → AnalysisAgent → AssessmentAnalysis → ReportingAgent → Report
```

The case-oriented layer is now also built during workflow execution and exposed through `AssessmentWorkflowResult.credit_case`:

```text
CreditAssessmentCase
        ↓
Deterministic section evidence
        ↓
FinalAssessment
        ↓
UI case overview / future case-level synthesis
```

The current LLM reporting path remains bounded: it may transform deterministic findings into prose but must not change status, thresholds, severity, evidence or limitations.

---

## 11. Presentation Layer

The Streamlit UI remains responsible for presentation and user interaction. It does not own credit-risk calculations.

The Results hierarchy is now:

```text
Executive Credit Assessment
          ↓
Credit Analysis Case
  ├── Customer Profile
  ├── Financial Analysis
  ├── Behavioural Analysis
  └── Debt Sustainability
          ↓
Final Deterministic Aggregation
          ↓
Risk Indicator Dashboard
          ↓
Audit Trail & Methodology
```

The four macro-area cards are intentionally descriptive at this stage. Areas without supplied data are shown as `NOT_EVALUABLE`; the UI does not fabricate inputs to make them appear assessed.

---

## 12. Roadmap Status

### Phase 1 — Case structure
**Completed.** Introduced `CreditAssessmentCase`, `AssessmentSection` and explicit macro-area boundaries.

### Phase 2 — Financial Analysis formalization
**Completed.** Existing R001–R007 rules are grouped into analyst-oriented dimensions without changing deterministic logic.

### Phase 3 — Behavioural Analysis
**Completed.** Added synthetic behavioural inputs and B001–B004 deterministic indicators, with case-level integration.

### Phase 4 — Debt Sustainability
**Completed.** Added DS001–DS003 cash-flow/debt-service indicators, tests and case-level integration. The implementation avoids duplication with existing financial indicators.

### Phase 5 — Customer Profile
**Completed.** Added structured customer/relationship context and deterministic EWS/restructuring flags.

### Phase 6 — Final Aggregation
**Completed.** Added explicit cross-section aggregation rules through `FinalAssessmentService`.

### Phase 7 — Executive Synthesis
**In progress.** The case is now exposed by the workflow and presented in the UI. The remaining work is to make `CaseAnalysisAgent` the formal downstream analysis contract for the complete case, then adapt the reporting prompts/generators to consume section-level evidence and `FinalAssessment`.

---

## 13. Architectural Boundary

```text
                  DETERMINISTIC CORE
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Customer Profile       Financial Analysis
              │                     │
              └──────────┬──────────┘
                         ▼
              Behavioural Analysis
                         │
                         ▼
               Debt Sustainability
                         │
                         ▼
                Final Assessment
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Deterministic output   LLM synthesis
              │                     │
              └──────────┬──────────┘
                         ▼
                   Executive Report
```

The deterministic core owns credit-risk evidence and decisions. AI is optional, replaceable and limited to interpretation and natural-language synthesis.
