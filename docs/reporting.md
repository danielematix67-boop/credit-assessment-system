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

`AssessmentAnalysis.customer_profile` is the authoritative source for the Customer Profile block in the Executive Narrative. The block is rendered deterministically from the full profile and is inserted by `ReportingAgent` after either the primary generator or the fallback returns. `material_customer_profile` remains available as a separately selected contextual subset, but it does not control the final Customer Profile block.

The materiality boundary is:

```text
Full CustomerProfileData
        ↓
CaseAnalysisAgent
        ↓
CustomerProfileMaterialityPolicy
        ├── material_customer_profile (bounded context for other uses)
        └── customer_profile (full fixed narrative block)
                    ↓
       ReportingAgent post-processing
                    ↓
            Executive Narrative
```

Materiality is therefore **not an LLM decision**. The reporting layer receives an already-selected contextual subset and can only format, organise or verbalise it.

Deterministic customer-profile rules remain in `rule_evidence` and retain their normal `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` semantics. Contextual fields such as active EWIs, business information, rating context or historical events are not converted into pseudo-rule findings merely because they are relevant to the Executive Summary.

Auxiliary one-to-many inputs from the `Shareholders`, `Credit Facilities` and `Relevant Events` sheets are converted into concise, human-readable records before they reach the narrative layer. The detailed Customer Profile analysis retains four canonical contextual sections in this order: **General Information**, **Risk Profile & Predictiveness**, **Relationship & Counterparty Context**, and **Relevant Events**. The analysis agent now writes these blocks as fluent prose rather than a sequence of bullet-style field labels. General Information begins with a natural introduction when company identity or business context is available; values such as ownership records, credit facilities and event details are verbalised using their domain meaning rather than raw `field=value` pairs. The detailed profile contract still preserves the four section identities for analysis and downstream mapping, including when a section has no populated values. The Executive Narrative is a separate, compact presentation: the deterministic generator flattens the selected material profile context into continuous prose and removes nested subsection headings to avoid excessive hierarchy inside the single `Customer Profile` paragraph. Missing fields are omitted; an otherwise empty detailed section states that no additional information is available. Small numeric values in date columns are not rendered as dates, preventing misplaced counts from becoming misleading dates near 1900. These records remain contextual information and do not create rule findings or change assessment status.

The detailed profile and the Executive Summary now use the same full factual profile block, while rule findings remain a separate subsequent part of the Customer Profile section:

| Output | Customer-profile scope |
|---|---|
| Detailed Customer Profile | Full available structured context |
| Executive Summary | Full deterministic profile context, followed by triggered rule findings |
| Rule evidence | Only deterministic rule results |
| LLM narrative | Prose generated from supplied evidence/context |

This prevents descriptive customer information from contaminating the deterministic rule-evidence contract while still making material customer context available to management-level reporting. The deterministic and AI reporting paths use the same fixed Customer Profile block, sourced from `AssessmentAnalysis.customer_profile`, and append triggered Customer Profile rule findings after it. The LLM-generated Customer Profile prose is replaced during post-processing, so its wording cannot change the fixed context. Both paths must emit exactly one Customer Profile heading.

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

Customer Profile is special: the complete deterministic contextual profile is placed first, independently of reporting mode, and triggered Customer Profile rule findings follow under a `Deterministic rule findings` label. The generated profile wording is not authoritative. If no profile context is available, the generator's normal Customer Profile behaviour applies.

### Finding ordering and thematic synthesis

Before the prompt is sent to the LLM, `ReportPromptBuilder` groups findings by their authoritative assessment area and applies a stable, domain-specific topic order. The current narrative order is:

| Assessment area | Topic sequence |
|---|---|
| Customer Profile | Customer Profile context and risk signals |
| Financial Analysis | Revenue and operating profitability → earnings quality and operating structure → working capital and cash conversion → leverage and funding structure → asset quality |
| Behavioural Analysis | Credit utilization and liquidity behaviour → payment behaviour → exposure evolution |
| Debt Sustainability | Debt-service capacity |

The ordering uses the configured rule-category metadata where available, not rule IDs. Unknown categories are retained after the recognized themes and preserve their relative source order. This is a presentation contract only: it does not reorder rule execution, change severity or affect assessment aggregation. The deterministic fallback applies the same topic priorities within each assessment-area paragraph: it sorts triggered finding sentences by rule-category metadata, preserves the original wording, and leaves unknown categories in stable source order after recognized topics. It does not paraphrase or synthesize findings, and it does not affect rule execution, severity or assessment aggregation.

The prompt labels each theme so the LLM can synthesize related concepts rather than restating every rule comment independently. For example, several working-capital findings may be expressed in connected prose about cash conversion and liquidity pressure, provided the individual indicators remain identifiable and no unsupported causal link is introduced. The model must preserve each deterministic indicator label verbatim and must not omit a triggered finding. Structural and evidence-coverage validation remain authoritative; a failed report follows the configured deterministic fallback path.

The narrative must:

- use only supplied deterministic evidence and selected Customer Profile context;
- preserve the meaning and identity of every mandatory finding;
- distinguish risk evidence from unavailable or non-evaluable evidence;
- avoid unsupported facts, causes, conclusions, recommendations or calculations;
- never generate or overwrite rule results, severity, section status or overall assessment status;
- preserve all four areas in both deterministic and LLM-generated reports;
- contain exactly one prose paragraph per area, with the canonical labels and fixed order;
- include the standard no-anomaly statement when an area has no triggered findings and no material contextual information.

### Narrative quality: synthesis without loss of evidence

The LLM prompt explicitly asks the model to **rewrite rather than transcribe** the source findings. The intended output is fluent, professional credit-monitoring prose, not a sequence of copied rule comments joined by repeated phrases such as “indicating” or “suggesting”.

The model may vary sentence openings, syntax and transitions, and may connect closely related findings in a sentence. It must retain the supplied finding order and keep every distinct signal identifiable. The explanatory wording can be paraphrased, but each deterministic indicator label must remain verbatim as an anchor. The model must not merge findings into a vague summary, introduce a causal relationship that the evidence does not state, or sacrifice coverage for brevity.

Customer Profile has an additional completeness requirement. The analysis agent constructs readable prose from the structured profile rather than emitting a bullet-style field inventory. The fixed Executive Narrative block includes all available context from **General Information**, **Risk Profile & Predictiveness**, **Relationship & Counterparty Context**, and **Relevant Events**, preserving supplied counterparty description, regulatory risk grades and their evolution, EWS signals, rating/PD, relationship information, ownership/management, credit facilities and relevant events. Nested subsection headings are removed. Risk-group interdependence/independence descriptions are intentionally omitted. Triggered deterministic rule findings are appended after this fixed block.

These are prompt-level generation requirements, not a change to the decision engine. They guide wording and organization only; the supplied findings remain the sole factual source, and structural/grounding validation plus deterministic fallback remain in place. Because language-model behaviour is not fully deterministic, prompt guidance should be backed by regression tests and realistic provider tests where available.

If the set of assessment domains changes, the narrative orchestration must derive its input from the workflow/domain contract rather than introducing rule-specific prompt branches.

## LLM provider normalization

LLM output is treated as untrusted text before it becomes part of the Executive Narrative. The reporting generator normalizes common provider-specific formatting before structural validation. In particular, Ollama/Qwen responses may contain internal `<think>...</think>` blocks or Markdown/numbered section headings; reasoning blocks are removed and supported heading variants are normalized to the canonical four-area structure. The prompt also requests explicit parser-friendly section markers. A response that still fails the structural contract is rejected and the deterministic reporting fallback is used.



### Narrow recovery for an omitted final heading

Small local models can occasionally return four blank-line-separated paragraphs while labeling only the first three assessment areas. The parser has a deliberately narrow recovery path for this shape: when the first three headings appear once and in canonical order, and exactly four non-empty paragraphs are present, the final unlabeled paragraph is assigned to **Debt Sustainability**. The first three labels are stripped as part of normalization. This is not a general relaxation of the contract: duplicated, misordered, partially missing or otherwise malformed headings remain invalid, and the recovered narrative must still pass the normal structural and evidence-grounding checks. If recovery or validation fails, deterministic reporting is used.

This normalization changes presentation only. It does not allow the model to alter deterministic status, severity, findings or materiality.\n\n## Grounding

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


## Centrale dei Rischi context in Behavioural Analysis

When the behavioural assessment provides a complete latest-CR snapshot (reference date, total system-wide utilised exposure and the three facility-type amounts), the Reporting Agent prepends a deterministic contextual sentence to the Behavioural Analysis paragraph. It is assembled from structured input, not generated by the LLM, and is therefore present in deterministic, LLM-primary and deterministic-fallback reporting paths. The sentence is included only when all required values are available and valid; missing context is not replaced with zero or inferred. Amounts are formatted in euros and the reference date is displayed as DD/MM/YYYY. This descriptive context does not create rule findings or affect assessment status.
