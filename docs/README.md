# Documentation

This directory contains the technical documentation for the assessment system.

## Documentation map

| Document | Purpose |
|---|---|
| [`architecture.md`](architecture.md) | System architecture, boundaries, configuration and workflow |
| [`rules.md`](rules.md) | Complete lifecycle for designing, implementing, testing and documenting a new rule |
| [`reporting.md`](reporting.md) | Deterministic evidence flow and bounded reporting |
| [`architecture-decisions.md`](architecture-decisions.md) | Accepted architectural decisions and rationale |
| [`adr-016-complete-rule-evidence-reporting.md`](adr-016-complete-rule-evidence-reporting.md) | Complete rule-evidence propagation into reporting |
| [`adr-017-rule-implementation-configuration-separation.md`](adr-017-rule-implementation-configuration-separation.md) | Separation between rule configuration and deterministic implementation |
| [`validation.md`](validation.md) | Validation levels, invariants, testing and CI |
| [`security-data-handling.md`](security-data-handling.md) | Input integrity, credentials, data minimization and LLM boundary |

## Recommended reading order

```text
README.md
   ↓
docs/architecture.md
   ↓
docs/rules.md
   ↓
docs/reporting.md
   ↓
docs/validation.md
   ↓
docs/security-data-handling.md
```

Architecture decisions provide the rationale behind the implementation and can be consulted when a design choice is being changed.

## Source-of-truth hierarchy

Documentation is descriptive. It is not the source of truth for the active rule inventory or decision policy.

```text
Rule catalogue / policy configuration
              ↓
      Configuration loaders
              ↓
Deterministic domain implementation
              ↓
     Assessment workflow
              ↓
          Reporting
              ↓
       Presentation
```

For rules, the active inventory is determined by valid domain YAML catalogues together with registered implementations discovered under `src/rules/`.

For final assessment, aggregation policy is defined by the final-assessment configuration and its policy model.

For CI, the workflow configuration is authoritative.

## Documentation maintenance principle

Prefer documenting **contracts, responsibilities and extension mechanisms** over copying the current contents of configuration files into Markdown.

Avoid maintaining lists such as:

- every active rule identifier;
- exact rule counts per domain;
- fixed threshold values;
- provider/model names that are merely deployment choices;
- exact coverage values when they belong to CI configuration.

Those values change more frequently than the architecture.

Use concrete identifiers or values only when they are required to explain an example, a business policy, a test boundary or a historical decision. Clearly label such values as examples or policy-specific values.

## Adding or changing a rule

Use [`rules.md`](rules.md). The guide covers:

```text
Business requirement
        ↓
Input contract
        ↓
Configuration
        ↓
Implementation
        ↓
Discovery / registry
        ↓
RuleResult
        ↓
Section / case aggregation
        ↓
Analysis evidence
        ↓
Reporting / grounding
        ↓
Demo / UI
        ↓
Tests
        ↓
Documentation
```

A rule change should not require rule-specific branches in the Reporting Agent or Streamlit presentation.

## Documentation quality check

Before merging documentation changes, verify that:

- referenced paths exist in the repository;
- described components still own the responsibilities assigned to them;
- configuration examples match the actual schema;
- examples are clearly distinguished from production catalogue values;
- removed legacy components are not presented as current architecture;
- reporting is described as downstream of deterministic assessment;
- rule inventory and policy values are not unnecessarily duplicated;
- links between related documents remain valid.
