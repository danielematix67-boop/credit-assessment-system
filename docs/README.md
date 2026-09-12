# Documentation

The documentation is organized around four complementary concerns: architecture, validation, security/data handling and architectural decisions.

## Documentation map

| Document | Purpose |
|---|---|
| [`architecture.md`](architecture.md) | Current system architecture, domain boundaries, workflow, Results UI and configuration model |
| [`architecture-decisions.md`](architecture-decisions.md) | Accepted architectural decisions and rationale |
| [`validation.md`](validation.md) | Test strategy, deterministic invariants, LLM grounding, resilience and CI gates |
| [`security-data-handling.md`](security-data-handling.md) | Input integrity, secrets, data minimization, LLM trust boundary and production limitations |

## Reading order

For a technical reviewer or supervisor, the recommended order is:

```text
README.md
   ↓
docs/architecture.md
   ↓
docs/architecture-decisions.md
   ↓
docs/validation.md
   ↓
docs/security-data-handling.md
```

## Current architectural message

The repository is intentionally built around one primary invariant:

> **The deterministic assessment decides; AI only explains.**

The current implementation contains four deterministic assessment domains:

- Customer Profile (`CP001–CP002`)
- Financial Analysis (`R001–R007`)
- Behavioural Analysis (`B001–B004`)
- Debt Sustainability (`DS001–DS003`)

These domains are consolidated by a deterministic final-assessment service. The Streamlit Results UI is a read-only presentation layer over the resulting evidence. Optional Gemini/Ollama reporting can generate narrative content, but provider failure or grounding failure activates deterministic fallback and cannot alter the credit decision.

## Documentation maintenance rule

Documentation should describe the **current implementation**, not planned architecture. In particular:

- rule configuration paths must match the files under `config/`;
- UI descriptions must match the current Results hierarchy;
- removed metrics or helpers must not be documented as active features;
- roadmap items must distinguish completed functionality from future work;
- deterministic decision boundaries must remain explicit whenever LLM functionality is described.
