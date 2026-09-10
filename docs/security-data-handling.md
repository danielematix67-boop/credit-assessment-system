# Security and Data Handling

## 1. Purpose

This document defines the security and data-handling principles for the `credit-assessment-system`.

The system processes credit-related financial information and can optionally use external generative AI services for narrative reporting. Security controls therefore focus on three distinct boundaries:

1. **Input boundary** — structured credit positions must satisfy basic integrity requirements before entering the assessment pipeline.
2. **Deterministic application layer** — processes structured credit information and performs the authoritative assessment.
3. **External LLM boundary** — may receive selected assessment information when LLM reporting is enabled.

The core principle is:

> **Sensitive data must be minimized before crossing an external service boundary, malformed input must be rejected before assessment, and the deterministic assessment must never depend on the external LLM.**

---

## 2. Input Integrity

The application validates the structural integrity of `CreditPosition` before deterministic rule evaluation.

The `CreditPositionValidator` rejects:

- invalid object types;
- empty `position_id` values;
- non-numeric values in numeric fields;
- boolean values where numeric values are expected;
- `NaN` and positive/negative infinity.

`None` is accepted because missing financial information can be a legitimate domain condition and is subsequently handled by rules through `NOT_EVALUABLE` where appropriate.

The generic validator intentionally does not enforce business-specific sign constraints. Such semantics remain under the control of the relevant credit-risk rule.

This boundary is structural rather than a substitute for full domain or business-policy validation.

---

## 3. Secrets Management

API credentials must never be hard-coded in source code, committed to Git, or embedded in configuration files tracked by the repository.

The application supports secret retrieval through:

- Streamlit secrets (`.streamlit/secrets.toml`);
- environment variables such as `GEMINI_API_KEY`.

The local Streamlit secrets file is explicitly excluded from version control.

Recommended practice:

```text
Secret
  ↓
Environment / Secret Store
  ↓
Application Configuration
  ↓
LLM Client
```

Never use:

```text
API Key
  ↓
Source Code / Git Repository
```

Credentials should also not be written to application logs, exception messages, screenshots, or generated reports.

---

## 4. Data Minimization

Only information required for the selected processing step should cross a system boundary.

The deterministic assessment should operate on the structured `CreditPosition` required by the rule engine.

When LLM reporting is enabled, the reporting layer should provide the model with the minimum structured information required to generate the narrative, such as:

- assessment status;
- deterministic key findings;
- relevant risk factors;
- documented limitations.

The LLM should not receive unrelated customer, account, or operational data merely because it is available to the application.

The preferred flow is:

```text
Credit Data
    │
    ▼
Input Validation
    │
    ▼
Deterministic Assessment
    │
    ▼
Selected Assessment Information
    │
    ▼
LLM Reporting Boundary
```

---

## 5. External LLM Boundary

External LLM providers represent a separate trust boundary from the deterministic credit-assessment engine.

The application must therefore treat generated content as untrusted external content.

The architectural rule is:

```text
Deterministic Assessment
        │
        ├──────────────► Structured Report Data
        │
        └──────────────► LLM Narrative Input
                              │
                              ▼
                         LLM Provider
                              │
                              ▼
                       Narrative Output
```

The LLM does not receive authority to:

- calculate the assessment status;
- change rule results;
- change severity;
- create structured findings;
- remove structured findings;
- change limitations;
- override deterministic business rules.

This limits the impact of model hallucinations or unexpected model behavior.

---

## 6. Local vs External LLM Execution

The project supports both external Gemini reporting and local Ollama reporting.

### Gemini

Gemini is an external service. Production use therefore requires an explicit data-governance decision concerning which data may leave the controlled environment, applicable contractual and regulatory requirements, provider data-processing terms, retention/logging policies and geographical or jurisdictional constraints.

### Ollama

Ollama can run locally and therefore provides an alternative deployment model for environments where external transmission of credit information is undesirable or prohibited.

Local execution does not automatically make a deployment secure: host access, network exposure, model files, logs, and operating-system permissions remain relevant security controls.

---

## 7. Prompt and Output Safety

Prompts should contain only controlled information from the deterministic assessment and should explicitly define the model's role as a reporting component.

Generated output must be treated as untrusted text.

The application must not execute model output as:

- Python code;
- SQL;
- shell commands;
- configuration;
- application instructions.

Generated text should remain presentation content.

The reporting path performs basic response/grounding validation where configured. More advanced semantic validation may be added in the future, but it must not transfer decision authority to the model.

---

## 8. Logging and Observability

Operational logging and execution metadata should support troubleshooting and traceability without exposing sensitive credit information or credentials.

The application records execution-level metadata for successfully completed workflows, including:

- unique execution identifier;
- UTC execution timestamp;
- reporting mode;
- generator used;
- fallback activation;
- classified reporting error category, when applicable;
- phase and total execution duration.

These fields are intended as provenance and diagnostic information. They must not be used as a substitute for structured credit data and must not contain customer identifiers or unnecessary financial details.

Avoid logging or exposing:

- API keys;
- authentication tokens;
- complete customer records;
- unnecessary financial details;
- complete prompts containing sensitive information;
- complete model responses when they may contain sensitive data;
- raw provider errors when they may contain credentials, tokens, or sensitive request data.

Where detailed diagnostic data is required, logs should use controlled identifiers and appropriate access restrictions.

Execution metadata is currently in-memory and attached to the workflow result; it is not a persistent audit trail. If durable observability is introduced, retention, access control, encryption, and data minimization requirements must be defined before implementation.

---

## 9. Data Retention

The application should follow a data-retention policy appropriate to the deployment environment.

The repository itself should contain only synthetic, anonymized, or otherwise non-sensitive demonstration data.

Production credit data should not be committed to Git or packaged into application artifacts.

If persistent storage is introduced in a future version, retention and deletion rules should be explicitly defined before implementation.

---

## 10. Access Control

Access to the application, repository, secrets, and operational infrastructure should follow least-privilege principles.

At minimum:

```text
User
  ↓
Application Access
  ↓
Required Functionality Only
```

Repository write access and secret-management permissions should be limited to users who require them.

LLM credentials should have the minimum permissions necessary for model invocation.

---

## 11. Security Invariants

### Input isolation

```text
Malformed CreditPosition
        ↓
     Rejected
        ↓
Rule Engine is not invoked
```

### Secret isolation

```text
Secrets ∉ Source Code
Secrets ∉ Git History
Secrets ∉ Logs
```

### Assessment isolation

```text
LLM Output
    ≠
Assessment Decision
```

### Data minimization

```text
External Service Input
    ⊆
Information Required for Reporting
```

### Structured-data integrity

```text
LLM Narrative
    ≠
Structured Assessment Data
```

### Fallback independence

```text
LLM Failure
    ↓
Deterministic Assessment remains valid
```

### Observability isolation

```text
Execution Metadata
    ≠
Assessment Decision
```

Execution metadata describes how the workflow completed; it does not influence rule evaluation or assessment status.

---

## 12. Security Validation Checklist

Before a production deployment, verify:

- [ ] No API keys or credentials are committed to the repository.
- [ ] `.streamlit/secrets.toml` and local environment files are excluded from version control.
- [ ] Demonstration data is synthetic or appropriately anonymized.
- [ ] Input validation rejects malformed and non-finite numeric data.
- [ ] External LLM transmission is explicitly approved for the intended data class.
- [ ] Prompts contain only required assessment information.
- [ ] LLM output is treated as untrusted text.
- [ ] LLM output cannot modify structured assessment fields.
- [ ] Execution metadata contains no unnecessary sensitive information.
- [ ] Logs do not expose credentials or unnecessary sensitive data.
- [ ] Access follows least-privilege principles.
- [ ] Deterministic fallback remains available when required by the deployment.
- [ ] Retention and deletion requirements are documented for production data.
- [ ] Persistent audit/observability storage, if introduced, has explicit retention and access controls.

---

## 13. Scope and Limitations

This document describes application-level security and data-handling principles. It is not a substitute for an organisation's information-security framework, data-classification policy, regulatory assessment, vendor due diligence, or production threat model.

For a banking deployment, the final security design must additionally consider the institution's requirements for data classification, access control, auditability, third-party risk, operational resilience, privacy, and regulatory compliance.

The current project is a technical portfolio/demo system. Production deployment would require infrastructure-level controls and formal security review in addition to the application-level controls described here.
