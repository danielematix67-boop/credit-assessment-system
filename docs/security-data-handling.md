# Security and Data Handling

## Why this matters

**In simple terms:** a credit-assessment system may handle information that is commercially or personally sensitive. The project therefore follows a simple principle: use only the data that is needed, protect credentials, and never let generated AI text change the underlying assessment.

**Technical meaning:** this document describes application-level controls for input integrity, secrets, data minimisation, LLM boundaries, metadata, retention and access.

> **The deterministic assessment never depends on an LLM.**

## What data should be used?

The repository is intended to contain only synthetic/anonymized demonstration data. Production credit data must not be committed to Git or packaged with the application.

**Synthetic data** is artificially created data used for demonstration or testing.

**Anonymized data** has been transformed according to an applicable anonymisation standard so that individuals or organisations cannot be identified from the resulting data. Simply removing a name or identifier is not necessarily sufficient to make data anonymous.

## Input integrity

**In simple terms:** before analysing a credit position, the system checks that the input is structurally valid. This prevents malformed values from entering the assessment path.

`CreditPositionValidator` runs before assessment and rejects invalid object types, empty identifiers, non-numeric values, booleans used as numbers, `NaN` and infinite values.

`None` can remain valid where a domain legitimately cannot evaluate a rule and therefore needs to produce `NOT_EVALUABLE`.

Structural validation does not replace business-specific rule validation. Both are necessary.

## Credentials and secrets

Credentials must stay outside source code and version control. They should be supplied through environment variables or the application's approved secret-management mechanism.

```text
Secret Store / Environment
          ↓
      Application
          ↓
       LLM Client
```

Never expose credentials in logs, screenshots, reports, commits or error messages.

## Data minimisation

**In simple terms:** do not send or store information merely because it is available. Send only what the next processing step actually needs.

For LLM reporting, only the assessment information required to generate the narrative should cross the provider boundary.

Production or confidential banking data must not be sent to an external provider without explicit authorisation and the applicable organisational, legal and governance controls.

## The AI boundary

The project can use an LLM to help write a human-readable report. The LLM is **not** the component that decides the credit assessment.

```text
Deterministic Assessment
        ↓
Required Evidence
        ↓
LLM Provider (if enabled)
        ↓
Narrative Report
```

Gemini is an external provider. Ollama can run locally. Both are reporting providers only.

The LLM cannot change assessment status, rule results, severity, findings or limitations. Generated text is untrusted presentation content and must not be executed as code, SQL, shell commands or configuration.

## Reporting failure does not mean assessment failure

If an LLM is unavailable or its output fails the applicable controls, the deterministic assessment remains valid.

Where configured, a deterministic fallback can produce the report without relying on the LLM.

```text
Assessment
   │
   ├── LLM available + valid output → narrative report
   │
   └── LLM unavailable/invalid       → deterministic fallback
```

The fallback is a reporting mechanism; it does not create a different credit decision.

## Logging and provenance

**Provenance** means information about how a run was executed.

Execution metadata may contain execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and timings.

This metadata is diagnostic. It is not a persistent audit trail unless a separate persistence and governance mechanism is introduced.

Avoid logging credentials, complete customer records, unnecessary financial data, sensitive prompts or sensitive provider responses.

## Data retention

The repository should contain only synthetic/anonymized demonstration data.

If persistent storage is introduced, retention and deletion requirements must be defined before implementation and aligned with the applicable organisational and regulatory framework.

## Access control

Apply least privilege to repository access, application access, credentials and infrastructure.

**Least privilege** means giving a person or component only the permissions needed to perform its intended task.

```text
User
 ↓
Application Access
 ↓
Required Functionality
```

## Security invariants

The main security expectations can be summarised as:

```text
Malformed Input → Rejected before assessment
Credentials     → Outside source code and Git
LLM Output      ≠ Assessment Decision
External Input  ⊆ Required Reporting Data
LLM Failure     → Deterministic Assessment remains valid
Metadata        ≠ Decision Evidence
```

## Deployment checklist

- [ ] No credentials are committed.
- [ ] Local secret/environment files are ignored.
- [ ] Demo data is synthetic/anonymized.
- [ ] Input validation rejects malformed and non-finite values.
- [ ] External LLM use is approved for the intended data class.
- [ ] Prompts contain only required assessment information.
- [ ] LLM output is treated as untrusted text.
- [ ] Structured assessment fields cannot be changed by the LLM.
- [ ] Logs and metadata avoid unnecessary sensitive information.
- [ ] Least-privilege access is applied.
- [ ] Deterministic fallback is available where required.
- [ ] Production retention requirements are documented before persistent storage is introduced.

## Scope limitation

This document covers application-level controls. It does not replace an organisation's security framework, regulatory assessment, vendor due diligence, privacy assessment or production threat model.
