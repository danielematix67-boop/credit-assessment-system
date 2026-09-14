# Reporting Architecture

## Purpose

The reporting layer converts deterministic credit-assessment evidence into concise analyst-oriented narrative.

> **The deterministic assessment decides; the Reporting Agent explains.**

Reporting is downstream of decisioning and has no authority over the credit judgement.

## Evidence Flow

```text
Four Domain Assessments
          ↓
Rule / Section Evidence
          ↓
Final Assessment
          ↓
Case Analysis
          ↓
AssessmentAnalysis
          ↓
Reporting Agent
      ↙          ↘
Deterministic   Optional LLM
 Generator      Gemini / Ollama
      ↘          ↙
         Report
```

The analysis layer preserves complete rule evidence from all four domains:

- Customer Profile — `CP001–CP003`
- Financial Analysis — `R001–R007`
- Behavioural Analysis — `B001–B004`
- Debt Sustainability — `DS001–DS003`

For each rule, the reporting path preserves `TRIGGERED`, `NOT_TRIGGERED` or `NOT_EVALUABLE`.

## AssessmentAnalysis

```text
AssessmentAnalysis
├── position_id
├── assessment_status
├── key_findings
├── risk_factors
├── limitations
└── rule_evidence
```

`key_findings` and `rule_evidence` carry the deterministic evidence used by reporting.

`risk_factors` is narrower and contains only high-severity triggered evidence.

`NOT_EVALUABLE` means that required evidence was unavailable or insufficient; it must not be narrated as normal credit quality.

## Reporting Boundary

The Reporting Agent may:

- organize supplied evidence;
- synthesize narrative;
- preserve material indicators and findings;
- use deterministic fallback.

It may not:

- evaluate or recalculate rules;
- change rule results or severity;
- change section or final status;
- invent unsupported evidence;
- replace `NOT_EVALUABLE` with `NORMAL`.

The structured assessment remains application-controlled and independent of generated prose.

## Generator Modes

| Generator | Role |
|---|---|
| Deterministic | Model-independent reporting |
| Gemini | Optional external narrative provider |
| Ollama | Optional local narrative provider |

```text
Evidence
   ↓
Primary Generator
   ↓
Grounding Check
 ↙             ↘
valid       invalid/failure
 ↓                ↓
Report      Deterministic Fallback
```

Provider failure or grounding failure can activate deterministic fallback without changing the underlying assessment.

## Narrative Contract

The application controls the Executive Narrative structure and domain order:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

The model supplies prose only. It must use supplied evidence, preserve material numerical information, avoid unsupported claims and never generate the structured assessment status.

## Testing

Reporting tests should verify:

1. evidence from all four domains is propagated;
2. all three rule outcomes are preserved;
3. `risk_factors` contains only high-severity triggered evidence;
4. prompts receive the complete evidence set;
5. generated prose cannot alter deterministic status;
6. provider and grounding failures activate deterministic fallback.

## Maintenance

New rule families must expose their evidence through the deterministic domain/case workflow. Reporting should consume aggregated evidence rather than implementing domain-specific rule logic.
