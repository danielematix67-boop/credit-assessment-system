# Security and Data Handling

## Scope

This project processes credit-assessment data and can optionally use Gemini or local Ollama for narrative reporting.

> **The deterministic assessment never depends on an LLM.**

## Input Integrity

`CreditPositionValidator` runs before assessment and rejects invalid object types, empty identifiers, non-numeric values, booleans used as numbers, `NaN` and infinite values.

`None` remains valid where the domain can legitimately return `NOT_EVALUABLE`.

Structural validation does not replace business-specific rule validation.

## Credentials

Credentials must remain outside source code and version control. Use environment variables or the application's secret-management mechanism.

```text
Secret Store / Environment
          ↓
      Application
          ↓
       LLM Client
```

Do not expose credentials in logs, screenshots, reports or error messages.

## Data Minimization

Only data required for the selected processing step should cross a system boundary.

For LLM reporting, send only the assessment information required for the narrative. Production or confidential banking data must not be sent to an external provider without explicit authorization and applicable governance controls.

## LLM Boundary

Gemini is an external provider. Ollama can run locally. Both are reporting providers only.

```text
Deterministic Assessment
        ↓
Selected Evidence
        ↓
LLM Provider
        ↓
Narrative
```

The LLM cannot change assessment status, rule results, severity, findings or limitations. Generated text is untrusted presentation content and must not be executed as code, SQL, shell commands or configuration.

## Logging and Provenance

Execution metadata may contain execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and timings.

It is diagnostic only and must not contain unnecessary sensitive information. The current metadata is in-memory and is not a persistent audit trail.

Avoid logging credentials, complete customer records, unnecessary financial data, sensitive prompts or sensitive provider responses.

## Data Retention

The repository should contain only synthetic/anonymized demonstration data. Production credit data must not be committed to Git or packaged with the application.

If persistent storage is introduced, retention and deletion rules must be defined before implementation.

## Access Control

Apply least privilege to repository access, application access, credentials and infrastructure.

```text
User
 ↓
Application Access
 ↓
Required Functionality
```

## Security Invariants

```text
Malformed Input → Rejected before assessment
Credentials     → Outside source code and Git
LLM Output      ≠ Assessment Decision
External Input  ⊆ Required Reporting Data
LLM Failure     → Deterministic Assessment remains valid
Metadata        ≠ Decision Data
```

## Deployment Checklist

- [ ] No credentials are committed.
- [ ] Local secret/environment files are ignored.
- [ ] Demo data is synthetic/anonymized.
- [ ] Input validation rejects malformed/non-finite values.
- [ ] External LLM use is approved for the intended data class.
- [ ] Prompts contain only required assessment information.
- [ ] LLM output is treated as untrusted text.
- [ ] Structured assessment fields cannot be changed by the LLM.
- [ ] Logs and metadata avoid unnecessary sensitive information.
- [ ] Least-privilege access is applied.
- [ ] Deterministic fallback is available where required.
- [ ] Production retention requirements are documented.

## Scope Limitation

This document covers application-level controls. It does not replace an organisation's security framework, regulatory assessment, vendor due diligence or production threat model.
