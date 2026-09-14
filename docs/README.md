# Documentation

This folder contains the concise technical documentation for the current implementation.

## Documentation map

| Document | Purpose |
|---|---|
| [`architecture.md`](architecture.md) | System architecture, domains, workflow, configuration and Results UI |
| [`reporting.md`](reporting.md) | Deterministic evidence flow and bounded reporting |
| [`architecture-decisions.md`](architecture-decisions.md) | Accepted architectural decisions and rationale |
| [`adr-016-complete-rule-evidence-reporting.md`](adr-016-complete-rule-evidence-reporting.md) | Complete rule-evidence propagation into reporting |
| [`adr-017-rule-implementation-configuration-separation.md`](adr-017-rule-implementation-configuration-separation.md) | Separation between rule configuration and deterministic implementation |
| [`validation.md`](validation.md) | Testing, invariants, scenario coverage and CI |
| [`security-data-handling.md`](security-data-handling.md) | Input integrity, secrets, data minimization and LLM boundary |

## Reading order

```text
README.md
   ↓
docs/architecture.md
   ↓
docs/reporting.md
   ↓
docs/architecture-decisions.md
   ↓
docs/validation.md
   ↓
docs/security-data-handling.md
```

## Current architecture

> **The deterministic assessment decides; AI only explains.**

The system evaluates four explicit domains:

- Customer Profile — `CP001–CP004`
- Financial Analysis — `R001–R007`
- Behavioural Analysis — `B001–B004`
- Debt Sustainability — `DS001–DS003`

The **18-rule** inventory is evaluated deterministically. The case-level assessment is produced before reporting. The analysis layer preserves complete rule evidence, including `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` outcomes.

Reporting consumes this evidence. Gemini and Ollama are optional providers; deterministic fallback remains available and LLM output cannot modify the assessment.

The Streamlit Results page is a read-only presentation layer with one authoritative macro-area evidence dashboard followed by the Executive Narrative.

## Documentation rule

Documentation must describe the repository as it exists on `main`.

- Keep paths aligned with the current source tree.
- Keep the rule catalogue aligned with configuration and implementation.
- Do not document removed legacy modules or duplicated UI sections.
- Keep deterministic decisioning separate from reporting.
- Mark future work as roadmap, not as implemented functionality.
- When adding or removing a rule, update catalogue counts, affected architecture/ADR references and the README rule-development workflow.
