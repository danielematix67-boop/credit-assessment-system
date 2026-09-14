# Architecture

## Overview

The system is a deterministic, multi-domain credit assessment with an optional AI-assisted reporting layer.

> **The deterministic system decides; AI explains.**

The four assessment domains are evaluated first and consolidated into a deterministic case assessment. Reporting runs only after the decision has been produced.

Core logic lives under `src/`; Streamlit presentation and application orchestration live under `app/`.

## System Flow

```text
CreditPosition + Domain Inputs
              ↓
      Structural Validation
              ↓
       Domain Assessments
   ┌──────────┼──────────┬──────────────┐
   ↓          ↓          ↓              ↓
Customer   Financial  Behavioural   Debt Sustainability
Profile    Analysis   Analysis
CP001–4    R001–7     B001–4        DS001–3
   └──────────┼──────────┴──────────────┘
              ↓
    CreditAssessmentCase
              ↓
    FinalAssessmentService
              ↓
      Final Assessment
              ↓
     Deterministic Analysis
              ↓
        Reporting Agent
          ↙          ↘
 Deterministic      Optional LLM
 Generator          Gemini / Ollama
          ↘          ↙
             Report
```

No LLM participates in the decision path.

## Assessment Domains

The current catalogue contains **18 rules**:

| Domain | Rules | Count |
|---|---|---:|
| Customer Profile | `CP001–CP004` | 4 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Canonical order:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

Each domain owns its inputs, rules and evidence. Cross-domain aggregation is handled separately by `FinalAssessmentService`.

## Deterministic Status Policy

For rule-based sections:

```text
2+ TRIGGERED                  → CRITICAL
1 TRIGGERED                   → ATTENTION
0 TRIGGERED + evaluable       → NORMAL
ALL NOT_EVALUABLE             → ATTENTION
EMPTY RESULTS                 → NORMAL
```

At case level:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 core ATTENTION section   → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward that threshold, while `CRITICAL` can still produce a `CRITICAL` case.

`NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.

## Validation Boundary

`CreditPositionValidator` runs before assessment and validates structural input integrity, including object type, identifier, numeric values, boolean misuse and finite values.

`None` can remain valid so rules can explicitly return `NOT_EVALUABLE`.

```text
Input
 ↓
Validation
 ↓
Rule Evaluation
 ↓
Section Results
 ↓
Final Assessment
```

Business-specific constraints remain in the relevant rule/domain implementation.

## Configuration

```text
config/
├── customer_profile_rules.yaml
├── financial_analysis_rules.yaml
├── behavioural_analysis_rules.yaml
├── debt_sustainability_rules.yaml
└── final_assessment.yaml
```

Thresholds, severity and aggregation policy are configuration-driven.

Rules are discovered and registered through the rule architecture rather than through central rule-specific branching.

## Reporting Boundary

Reporting consumes structured deterministic evidence from all four domains.

The LLM may synthesize narrative, but cannot change:

- rule results;
- thresholds;
- severity;
- findings;
- limitations;
- section status;
- final status.

Supported modes are deterministic reporting, Gemini with fallback and Ollama with fallback.

```text
Deterministic Evidence
        ↓
Primary Generator
        ↓
Grounding Validation
    ↙           ↘
 valid        invalid/failure
   ↓               ↓
 Report      Deterministic Fallback
```

Provider or grounding failure changes only the reporting path, never the assessment.

## Results UI

The Results page follows a compact hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

The macro-area dashboard is the authoritative deterministic evidence surface. Technical inspection is progressively disclosed through **Rule Catalogue & Filters** and **Individual Rule Detail**.

Separate bottom-of-page Risk Drivers and Detailed Assessment sections are not rendered.

The UI is presentation-only and does not recalculate assessment logic.

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   ├── input/
│   │   └── results/
│   └── workflow/
├── config/
├── src/
│   ├── agents/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   ├── rules/
│   │   ├── base/
│   │   ├── customer_profile/
│   │   ├── financial_analysis/
│   │   ├── behavioural/
│   │   └── sustainability/
│   └── services/
├── docs/
└── tests/
```

The old legacy rule trees, `tests/ui/` and `app/ui/credit_position.py` compatibility module are not part of the current architecture.

## Demo Data

Demo scenarios are synthetic/anonymized and exercise the four assessment domains and configured rule inventory, including Customer Profile forborne exposure. Production or confidential banking data must not be committed to the repository.

## Execution Metadata

Workflow metadata records provenance such as execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and timings.

It is observational only and does not participate in credit decisioning.

## Quality Boundary

GitHub Actions targets **Python 3.14** and runs:

```text
Ruff → Mypy → Pytest + coverage
```

The coverage gate is **95% for `src`**.

## Architectural Invariants

1. Deterministic rules own credit decisions.
2. All four domains remain explicit.
3. `NOT_EVALUABLE` is not treated as `NOT_TRIGGERED`.
4. Rule policy is configuration-driven.
5. Reporting consumes structured evidence rather than implementing rule logic.
6. LLM providers are optional and replaceable.
7. LLM failure cannot invalidate the deterministic assessment.
8. Streamlit does not own business logic.
9. Execution metadata is observational.
10. The Results page has one authoritative macro-area evidence surface.
