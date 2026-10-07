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

## Customer Profile reporting

Customer Profile is a structured contextual input to reporting and is deliberately separated from rule-level evidence.

`AssessmentAnalysis.customer_profile` contains the full structured profile used for the detailed Customer Profile presentation. It is represented through four ordered sections:

1. General Information
2. Risk Profile & Predictiveness
3. Relationship & Counterparty Context
4. Relevant Events

`AssessmentAnalysis.material_customer_profile` contains the subset selected for Executive Summary reporting. The selection is performed by `CustomerProfileMaterialityPolicy` in the deterministic analysis layer. The policy deliberately excludes profile fields already represented by deterministic Customer Profile rules (currently CP001–CP005), so the same fact is not rendered twice in the Executive Narrative.

The materiality boundary is:

```text
Full CustomerProfileData
        ↓
CaseAnalysisAgent
        ↓
CustomerProfileMaterialityPolicy
        ↓
material_customer_profile
        ↓
ReportPromptBuilder / DeterministicReportGenerator
        ↓
Executive Narrative
```

Materiality is therefore **not an LLM decision**. The reporting layer receives an already-selected contextual subset and can only format, organise or verbalise it.

Deterministic customer-profile rules remain in `rule_evidence` and retain their normal `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` semantics. Contextual fields such as active EWIs, business information, rating context or historical events are not converted into pseudo-rule findings merely because they are relevant to the Executive Summary.

The detailed profile and the Executive Summary intentionally have different scopes:

| Output | Customer-profile scope |
|---|---|
| Detailed Customer Profile | Full available structured context |
| Executive Summary | Deterministically selected material context |
| Rule evidence | Only deterministic rule results |
| LLM narrative | Prose generated from supplied evidence/context |

This prevents descriptive customer information from contaminating the deterministic rule-evidence contract while still making material customer context available to management-level reporting. The deterministic and AI reporting paths also merge Customer Profile rule findings and material contextual information into a single `Customer Profile` Executive Narrative section; they must not emit duplicate Customer Profile headings.

## Reporting boundary

The Reporting Agent may:

- organise supplied evidence;
- synthesise narrative;
- preserve material indicators and findings;
- verbalise the deterministic material customer-profile context supplied to it;
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

Every Executive Narrative contains the same four assessment areas, in the following fixed order:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

A section is never omitted because no rule is triggered. When an area contains no triggered deterministic evidence, the report explicitly states that no anomalies were identified by the configured assessment rules in that area. This makes a NORMAL assessment readable as a complete review rather than as a report containing only the areas with exceptions.

Customer Profile is special because material contextual information may be present even when no Customer Profile rule is triggered. In that case, the section contains the deterministic contextual profile followed by any triggered findings; if neither is available, it uses the standard no-anomaly statement.

The narrative must:

- use the supplied deterministic evidence;
- preserve material numerical information;
- distinguish risk from unavailable evidence;
- avoid unsupported factual claims;
- never generate or overwrite the structured assessment status;
- preserve the four-area structure in both deterministic and LLM-generated reports.\n- contain exactly one prose paragraph for each area.\n- keep the authoritative assessment-area order: Customer Profile, Financial Analysis, Behavioural Analysis, Debt Sustainability.

If the set of assessment domains changes, the narrative orchestration must derive its input from the workflow/domain contract rather than introducing rule-specific prompt branches.

## LLM provider normalization\n\nLLM output is treated as untrusted text before it becomes part of the Executive Narrative. The reporting generator normalizes common provider-specific formatting before structural validation. In particular, Ollama/Qwen responses may contain internal `<think>...</think>` blocks or Markdown/numbered section headings; reasoning blocks are removed and supported heading variants are normalized to the canonical four-area structure. The prompt also requests explicit parser-friendly section markers. A response that still fails the structural contract is rejected and the deterministic reporting fallback is used.\n\nThis normalization changes presentation only. It does not allow the model to alter deterministic status, severity, findings or materiality.\n\n## Grounding

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
4. prompts receive the complete evidence set required by the contract, including the selected material customer-profile context;
5. generated prose cannot alter deterministic status or customer-profile materiality selection;
6. every report contains all four required assessment areas, including for NORMAL scenarios with no triggered rules;
7. unsupported or altered material evidence is rejected by grounding;
8. provider and grounding failures activate deterministic fallback;
9. fallback failure is surfaced rather than silently hidden.

## Maintenance principles

- Keep reporting independent of rule identifiers.
- Keep prompts independent of thresholds and decision logic.
- Consume aggregated structured evidence instead of importing individual rule implementations.
- Treat the configured assessment catalogue as the source of truth for the active rule set.
- Update documentation when the reporting contract changes, not when individual rule counts change.
