# Reporting Architecture

## 1. Purpose

The reporting layer converts deterministic credit-assessment evidence into an analyst-oriented narrative. It is intentionally downstream of decisioning and has **no authority over the credit judgement**.

> **The Rule Engine decides; the Reporting Agent explains.**

This boundary applies to every configured assessment domain:

- Customer Profile (`CP001–CP002`)
- Financial Analysis (`R001–R007`)
- Behavioural Analysis (`B001–B004`)
- Debt Sustainability (`DS001–DS003`)

The current reporting pipeline receives the complete deterministic rule evidence, not only triggered findings.

## 2. Evidence Flow

```text
Domain Services
      ↓
RuleResult[] / Section Evidence
      ↓
Final Assessment
      ↓
CaseAnalysisAgent
      ↓
Complete Rule Evidence
      ↓
AssessmentAnalysis
      ↓
ReportingAgent
      ↓
Deterministic / Gemini / Ollama Generator
      ↓
Report
```

`CaseAnalysisAgent` is the aggregation boundary between deterministic assessment and narrative reporting. For each rule result it preserves the rule outcome as analysis evidence, including:

- `TRIGGERED` rules;
- `NOT_TRIGGERED` rules;
- `NOT_EVALUABLE` rules.

Consequently, the reporting layer can describe the complete assessment picture across all macro-areas rather than seeing only the risk signals.

## 3. `AssessmentAnalysis` Contract

`AssessmentAnalysis` contains the deterministic status plus reporting evidence:

```text
AssessmentAnalysis
├── position_id
├── assessment_status
├── key_findings
├── risk_factors
├── limitations
└── rule_evidence
```

`key_findings` is the reporting input and currently contains the complete deterministic rule evidence aggregated by `CaseAnalysisAgent`. `rule_evidence` exposes the same complete evidence explicitly for consumers that need a dedicated field.

`risk_factors` remains intentionally narrower: it contains only high-severity triggered rules. This prevents the narrative layer from treating every rule as a risk driver.

## 4. Evidence Semantics

The reporting layer preserves the distinction between rule outcomes:

| Rule outcome | Reporting meaning |
|---|---|
| `TRIGGERED` | A deterministic risk condition was detected |
| `NOT_TRIGGERED` | The rule was evaluated and did not detect its configured risk condition |
| `NOT_EVALUABLE` | Required evidence was unavailable or insufficient |

`NOT_EVALUABLE` must never be narrated as evidence of normal credit quality.

For triggered rules, existing deterministic rule/comment text is reused where available. The reporting analysis does not expose internal rule thresholds merely to construct a narrative.

## 5. Reporting Agent Boundary

The Reporting Agent can:

- organize supplied deterministic evidence;
- synthesize an executive narrative;
- describe risk drivers supplied by the analysis layer;
- preserve supplied indicator values and findings;
- use a deterministic fallback when the primary generator fails.

It cannot:

- recalculate a rule;
- change a rule result;
- change severity;
- change section status;
- change the final assessment;
- invent unsupported evidence;
- replace `NOT_EVALUABLE` with `NORMAL`.

The structured assessment remains application-controlled and is displayed independently of generated prose.

## 6. Generator Paths

```text
                    ReportingAgent
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      Deterministic              Optional LLM
       Generator               Gemini / Ollama
             │                       │
             │                Grounding checks
             │                       │
             └───────────┬───────────┘
                         ▼
                       Report
                         │
                  deterministic
                    fallback
```

The deterministic generator provides a model-independent reporting path. Gemini and Ollama are optional narrative providers. Provider failure or invalid grounding can switch the reporting path to deterministic fallback without changing the underlying assessment.

## 7. Prompt Grounding

The prompt builder consumes `AssessmentAnalysis.key_findings`. Because this collection is populated with complete rule evidence, the prompt receives rule outcomes from every configured domain.

The prompt contract requires the model to use supplied evidence, preserve material numerical information, avoid unsupported causal claims and never generate the structured assessment status.

Internal rule identifiers are not intended for end-user narrative output.

## 8. Testing Implications

The reporting architecture should be protected by regression tests that verify:

1. evidence from all four domains reaches `AssessmentAnalysis`;
2. `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` outcomes are preserved;
3. `risk_factors` contains only high-severity triggered evidence;
4. the reporting prompt receives the complete evidence set;
5. the generated report cannot alter deterministic status;
6. LLM failure and grounding failure activate deterministic fallback.

The architectural invariant is:

```text
Complete deterministic evidence
            ↓
     AssessmentAnalysis
            ↓
       ReportingAgent
            ↓
     Narrative only
```

## 9. Maintenance Rule

Whenever a new assessment domain or rule family is introduced, the domain service must expose its deterministic evidence through the case workflow. Reporting should consume the aggregated evidence rather than adding domain-specific rule logic to the Reporting Agent.

This keeps the reporting layer scalable: adding a rule changes the deterministic evidence inventory, not the decision authority or the reporting architecture.
