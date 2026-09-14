# Reporting Architecture

## Purpose

The reporting layer converts deterministic credit-assessment evidence into concise analyst-oriented narrative.

> **The deterministic assessment decides; the Reporting Agent explains.**

Reporting is downstream of decisioning and has no authority over the credit judgement.

## Evidence flow

```text
Domain assessments
        ↓
Rule / section evidence
        ↓
Final assessment
        ↓
Case analysis
        ↓
AssessmentAnalysis
        ↓
Reporting Agent
      ↙          ↘
Deterministic   Optional LLM
 generator       provider
      ↘          ↙
         Report
```

The analysis layer preserves the rule evidence produced by the configured domain assessments. The reporting layer is therefore independent of the number, identifiers or names of individual rules.

## AssessmentAnalysis

The analysis contract contains the deterministic assessment context and reporting evidence, including:

```text
AssessmentAnalysis
├── position_id
├── assessment_status
├── key_findings
├── risk_factors
├── limitations
└── rule_evidence
```

`rule_evidence` carries the complete rule-level evidence available from the assessment workflow.

`key_findings` provides the findings used for narrative synthesis. `risk_factors` is a narrower reporting view focused on high-severity triggered evidence.

`NOT_EVALUABLE` means required evidence was unavailable or insufficient. It must remain distinguishable from an evaluated rule that did not trigger.

## Reporting boundary

The Reporting Agent may:

- organise supplied evidence;
- synthesise narrative;
- preserve material indicators and findings;
- use deterministic fallback.

It may not:

- evaluate or recalculate rules;
- change rule results or severity;
- change section or final status;
- invent unsupported evidence;
- replace unavailable evidence with an assertion of normality.

The structured assessment remains application-controlled and independent of generated prose.

## Generator modes

The application exposes a deterministic reporting path and may expose one or more configured LLM providers depending on the execution environment.

```text
Deterministic evidence
        ↓
Configured primary generator
        ↓
Grounding validation
     ↙          ↘
 valid       invalid/failure
  ↓               ↓
Report      Deterministic fallback
```

Provider configuration belongs to the application environment. Documentation should not assume that a particular provider or model is always available.

## Narrative contract

The application controls the structure and ordering of the Executive Narrative. The model supplies prose only.

The narrative must:

- use the supplied deterministic evidence;
- preserve material numerical information;
- distinguish risk from unavailable evidence;
- avoid unsupported factual claims;
- never generate or overwrite the structured assessment status.

If the set of assessment domains changes, the narrative orchestration must derive its input from the workflow/domain contract rather than introducing rule-specific prompt branches.

## Grounding

Generated narrative is treated as untrusted output. Grounding validation protects deterministic facts, particularly material indicator values and findings.

```text
Structured evidence
        ↓
Generated narrative
        ↓
Grounding checks
        ↓
Accepted report OR deterministic fallback
```

Grounding failure is a reporting failure, not a credit-assessment failure.

## Adding a rule

A new rule should require no change to the Reporting Agent merely to make its evidence visible. The normal path is:

```text
New rule
  ↓
RuleResult
  ↓
Section evidence
  ↓
Case analysis
  ↓
AssessmentAnalysis.rule_evidence
  ↓
Reporting
```

If a new rule introduces a genuinely new evidence type or changes a reporting contract, update the relevant structured model and tests. Do not add a prompt-side implementation of the rule.

See [`rules.md`](rules.md) for the complete rule-development checklist.

## Testing

Reporting tests should verify:

1. configured domain evidence is propagated;
2. all supported rule outcomes remain distinguishable;
3. high-severity triggered evidence is correctly represented as a risk factor;
4. prompts receive the complete evidence set required by the contract;
5. generated prose cannot alter deterministic status;
6. unsupported or altered material evidence is rejected by grounding;
7. provider and grounding failures activate deterministic fallback;
8. fallback failure is surfaced rather than silently hidden.

## Maintenance principles

- Keep reporting independent of rule identifiers.
- Keep prompts independent of thresholds and decision logic.
- Consume aggregated structured evidence instead of importing individual rule implementations.
- Treat the configured assessment catalogue as the source of truth for the active rule set.
- Update documentation when the reporting contract changes, not when individual rule counts change.
