# Documentation

This directory contains the project documentation. It is designed for **two audiences at the same time**:

- people who want to understand the business idea without being software specialists;
- technical readers who need an accurate description of the architecture and implementation contracts.

You do **not** need to understand Python, machine learning or Large Language Models to start reading this documentation.

## Start here

If this is your first time seeing the project, read in this order:

```text
README.md
   ↓
getting-started.md
   ↓
glossary.md
   ↓
architecture.md
   ↓
reporting.md
```

The [glossary](glossary.md) is useful whenever a technical or credit-risk term is unfamiliar.

## Documentation map

| Document | What you will learn |
|---|---|
| [`getting-started.md`](getting-started.md) | How to understand, install and run the project for the first time |
| [`glossary.md`](glossary.md) | Plain-language and technical definitions of the main project terms |
| [`architecture.md`](architecture.md) | How the system is organised and how information moves through it |
| [`rules.md`](rules.md) | How a credit-risk rule is defined, implemented, tested and extended |
| [`reporting.md`](reporting.md) | How deterministic assessment evidence becomes a human-readable report |
| [`validation.md`](validation.md) | What the system validates and how correctness is tested |
| [`security-data-handling.md`](security-data-handling.md) | How input integrity, credentials, data minimisation and AI boundaries are handled |
| [`architecture-decisions.md`](architecture-decisions.md) | Important architectural decisions and the reasons behind them |
| [`adr-016-complete-rule-evidence-reporting.md`](adr-016-complete-rule-evidence-reporting.md) | Why complete rule evidence is propagated into reporting |
| [`adr-017-rule-implementation-configuration-separation.md`](adr-017-rule-implementation-configuration-separation.md) | Why rule configuration is separated from rule implementation |

## Choose your path

### I am not technical

Start with:

```text
README.md
   ↓
getting-started.md
   ↓
glossary.md
   ↓
architecture.md
   ↓
reporting.md
```

Focus on these questions:

1. What problem does the system solve?
2. What information does it analyse?
3. How does it decide whether a condition is relevant?
4. Why is the decision deterministic?
5. What does the AI do, and what is it not allowed to do?

### I am a developer

Start with:

```text
architecture.md
   ↓
rules.md
   ↓
validation.md
   ↓
reporting.md
   ↓
security-data-handling.md
   ↓
ADRs
```

### I am reviewing the project as a thesis, portfolio or architecture case study

The most useful path is:

```text
Business problem
   ↓
System architecture
   ↓
Deterministic / AI boundary
   ↓
Rule lifecycle
   ↓
Validation and testing
   ↓
Security and data handling
   ↓
Architectural decisions
```

## The central idea

The simplest way to understand the project is:

```text
                 CREDIT ASSESSMENT
                        │
                        ▼
             DETERMINISTIC ENGINE
                        │
             "What is the result?"
                        │
                        ▼
              STRUCTURED EVIDENCE
                        │
                        ▼
                  AI REPORTING
                        │
              "How do we explain it?"
                        │
                        ▼
                     REPORT
```

The deterministic part of the system is responsible for the assessment and its evidence. The AI layer can turn that evidence into natural language, but it cannot replace or change the underlying assessment.

> **The deterministic system decides; AI explains.**

## How to read technical terms

The documentation uses a two-level explanation whenever a concept is important:

> **In simple terms:** what the concept means from a business or user perspective.
>
> **Technical meaning:** what the concept means inside the software.

For example, a **rule** is simply an automatic risk check. Technically, it is a deterministic implementation that evaluates configured input and produces a structured `RuleResult`.

If a term such as `RuleResult`, registry, discovery, grounding or fallback is unfamiliar, use [`glossary.md`](glossary.md) before continuing.

## Source of truth

Documentation explains the system, but it is **not** the source of truth for values that change as the project evolves.

```text
Configuration / policy
          ↓
Configuration loaders
          ↓
Deterministic implementation
          ↓
Assessment workflow
          ↓
Reporting
          ↓
Presentation
```

For example, the active rule catalogue is defined by the valid configuration catalogues together with the registered deterministic implementations. Final-assessment behaviour is governed by its configuration and policy model. CI configuration is authoritative for automated quality gates.

This is why the documentation intentionally avoids duplicating volatile details such as the complete current rule inventory, exact rule counts, individual thresholds, provider choices or coverage percentages.

## Extending the system

Adding a new rule is an end-to-end change, not simply a new line in a YAML file:

```text
Business requirement
        ↓
Input contract
        ↓
Configuration
        ↓
Deterministic implementation
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
Tests
        ↓
Documentation
```

See [`rules.md`](rules.md) for the complete procedure.

A healthy extension should not require rule-specific branches in the Reporting Agent or presentation layer merely because a new rule identifier has been introduced.

## Documentation maintenance principles

Good documentation should remain useful when the catalogue evolves. Prefer documenting:

- concepts and business meaning;
- stable interfaces and contracts;
- component responsibilities;
- data flow and boundaries;
- extension mechanisms;
- architectural rationale;
- security invariants;
- validation principles.

Avoid duplicating values that have a more authoritative source elsewhere.

When a concrete value is necessary, clearly identify whether it is:

- an example;
- a current configuration value;
- a policy requirement;
- a test-specific value;
- a historical decision.

## Documentation quality checklist

Before changing documentation, verify that:

- the explanation is understandable without specialist knowledge where possible;
- technical terminology is defined before it becomes essential to understanding;
- business meaning and technical implementation are not conflated;
- described responsibilities match the actual architecture;
- configuration examples match the actual schema;
- examples are clearly distinguished from production values;
- obsolete components are not described as current architecture;
- deterministic assessment remains clearly separated from AI reporting;
- `NOT_EVALUABLE` is not described as equivalent to a normal result;
- links point to maintained documents;
- volatile inventories and configuration values are not unnecessarily copied into Markdown.
