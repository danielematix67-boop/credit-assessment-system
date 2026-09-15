# Glossary

This glossary explains the main terms used by the project in two ways:

- **In simple terms:** what the concept means for a reader who does not work with software or AI.
- **Technical meaning:** how the concept is used inside the system.

The goal is to make the documentation accessible without reducing technical precision.

## Credit Risk concepts

### Credit Position

**In simple terms:** The customer or credit relationship being analysed by the system.

**Technical meaning:** The structured input object that contains the information required by the assessment workflow.

### Credit Assessment

**In simple terms:** The result of checking a credit position against a set of risk criteria.

**Technical meaning:** A structured deterministic result produced by applying configured rules and aggregation policies to validated input data.

### Domain

**In simple terms:** A specific area of the credit analysis, such as financial or behavioural information.

**Technical meaning:** A logical assessment area containing related indicators, rules and results. Domain membership is configuration- and implementation-dependent and should not be confused with a fixed list of current catalogue entries.

### Indicator

**In simple terms:** A number or piece of information used to evaluate a credit position.

**Technical meaning:** An input or derived value consumed by one or more deterministic rules.

### Threshold

**In simple terms:** A limit used to determine whether an indicator represents a relevant condition.

**Technical meaning:** A configured comparison value used by a rule. Thresholds belong to the rule configuration and are not hard-coded into reporting or presentation logic.

### Rule

**In simple terms:** An automatic check that asks whether a specific risk condition is present.

**Technical meaning:** A deterministic implementation that evaluates a configured condition and returns a structured `RuleResult`.

### Rule Result

**In simple terms:** The structured answer produced by one risk check.

**Technical meaning:** The output of a rule evaluation, including its status and the evidence required by downstream assessment and reporting components.

### Triggered

**In simple terms:** The rule found the condition it was designed to detect.

**Technical meaning:** `RuleResult` has status `TRIGGERED`. This is evidence of a configured condition, not by itself the final credit decision.

### Not Triggered

**In simple terms:** The check was possible, but the risk condition was not found.

**Technical meaning:** `RuleResult` has status `NOT_TRIGGERED`.

### Not Evaluable

**In simple terms:** There was not enough valid information to perform the check.

**Technical meaning:** `RuleResult` has status `NOT_EVALUABLE`. It must remain distinguishable from `NOT_TRIGGERED`; absence of evidence is not evidence of normality.

### Severity

**In simple terms:** How important a detected condition is from a risk perspective.

**Technical meaning:** A deterministic classification associated with rule evidence and governed by the configured rule/policy contract.

### Evidence

**In simple terms:** The information that explains why the system reached a particular result.

**Technical meaning:** Structured deterministic information propagated from rule evaluation through section/case assessment into analysis and reporting.

## Software architecture concepts

### Deterministic

**In simple terms:** Given the same valid information and the same settings, the system produces the same result.

**Technical meaning:** The assessment path is reproducible for a fixed input and configuration and does not depend on an LLM response, provider availability or UI state.

### Rule Engine

**In simple terms:** The part of the system that performs the automatic risk checks.

**Technical meaning:** The deterministic layer responsible for resolving configured rules and evaluating them against the assessment input.

### Configuration-driven

**In simple terms:** Important behaviour is described in configuration rather than being hidden inside application code.

**Technical meaning:** Rule and assessment parameters are loaded from configuration files and interpreted by deterministic components.

### Configuration Loader

**In simple terms:** The component that reads the system's configuration and makes it usable by the application.

**Technical meaning:** A component that parses and validates configuration data before it is used to construct deterministic assessment objects.

### Registry

**In simple terms:** A lookup mechanism that tells the system which implementation corresponds to a rule identifier.

**Technical meaning:** The rule registry resolves configured identifiers to registered `Rule` classes after rule discovery.

### Discovery

**In simple terms:** The mechanism that finds available rule implementations automatically.

**Technical meaning:** The process that imports/discovers rule modules so implementations can self-register and be resolved without maintaining a central list of imports for ordinary rule additions.

### Aggregation

**In simple terms:** Combining the results of several checks to obtain a result for a larger part of the analysis.

**Technical meaning:** Deterministic services combine rule-level results into section-level and case-level assessment results according to the configured policy.

### Policy

**In simple terms:** The agreed logic used to decide how individual findings contribute to an overall result.

**Technical meaning:** A deterministic set of aggregation rules, including final-assessment behaviour, externalised where appropriate in configuration and policy models.

### Workflow

**In simple terms:** The sequence of steps the system follows from input to final report.

**Technical meaning:** The orchestration that validates input, executes domain assessments, aggregates results, creates deterministic analysis evidence and invokes reporting.

## AI and reporting concepts

### LLM

**In simple terms:** An AI model that can generate and transform natural-language text.

**Technical meaning:** A Large Language Model used by this project only as a downstream reporting component. It does not own deterministic credit decisioning.

### Reporting

**In simple terms:** Turning the structured assessment results into a human-readable explanation or report.

**Technical meaning:** A downstream layer that consumes deterministic evidence and produces narrative output through a primary generator and, where required, a deterministic fallback.

### Grounding

**In simple terms:** Checking that an AI-generated explanation remains faithful to the information supplied by the assessment engine.

**Technical meaning:** Validation that generated material, especially material indicators and findings, is supported by the authoritative deterministic evidence.

### Fallback

**In simple terms:** A backup way of producing the report when the preferred AI path cannot be used safely or successfully.

**Technical meaning:** A deterministic reporting path activated by defined provider, generation or grounding failures. A reporting failure must not invalidate the underlying deterministic assessment.

### Primary Generator

**In simple terms:** The preferred component used to generate the narrative report.

**Technical meaning:** The selected reporting generator, which may use an LLM provider when configured and available.

### Untrusted Output

**In simple terms:** Text produced by an external or probabilistic component that must not automatically be treated as fact or executable instructions.

**Technical meaning:** LLM-generated text is presentation content. It cannot modify structured assessment fields and must not be executed as code, SQL, shell commands or configuration.

## Validation and testing concepts

### Structural Validation

**In simple terms:** Checking that the input has the correct basic shape and contains acceptable values before analysis begins.

**Technical meaning:** Validation performed before assessment to reject invalid types, missing identifiers where required, booleans used as numbers, non-finite numeric values and other malformed input conditions.

### Unit Test

**In simple terms:** A test of one small part of the system.

**Technical meaning:** A test focused on an individual rule, validator, service, model or policy component.

### Integration Test

**In simple terms:** A test that checks whether multiple components work correctly together.

**Technical meaning:** A test covering cross-layer behaviour such as evidence propagation and aggregation.

### End-to-End / Scenario Test

**In simple terms:** A test that follows a realistic case through the system.

**Technical meaning:** A test that exercises representative combinations of input, domains, rule outcomes, aggregation and reporting behaviour.

### CI

**In simple terms:** Automated checks that run when the repository changes.

**Technical meaning:** Continuous Integration workflows that execute repository quality gates such as linting, type checking and automated tests.

## Data and security concepts

### Synthetic Data

**In simple terms:** Artificial data created for demonstration or testing rather than copied from real customers.

**Technical meaning:** Non-production data designed to exercise the application without exposing real banking information.

### Anonymized Data

**In simple terms:** Data processed so that it no longer directly identifies a person or organisation, subject to the applicable anonymisation standard.

**Technical meaning:** Data transformed according to an approved anonymisation process. Anonymisation claims must follow the relevant organisational and regulatory standard; simply removing a name is not necessarily sufficient.

### Data Minimization

**In simple terms:** Send and store only the information that is actually needed.

**Technical meaning:** Limiting data crossing system boundaries, especially when evidence is sent to an external LLM provider.

### Provenance

**In simple terms:** Information about how a result was produced.

**Technical meaning:** Execution metadata such as execution identity, timestamp, reporting mode, generator/fallback state, errors and timings. Provenance is diagnostic metadata and is not decision evidence.

## Core principle

The project can be summarized by one rule:

```text
Deterministic system → decides and provides evidence
AI layer             → explains that evidence
Presentation layer   → displays the result
```

The AI layer must never become an alternative source of truth for the credit assessment.
