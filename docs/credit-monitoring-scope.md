# Credit Quality Monitoring: Business Scope and Analytical Framework

## Purpose and positioning

Credit Assessment System is a prototype **credit-quality monitoring and analytical-support tool**. Its purpose is to organise and automate selected checks on a counterparty's credit-risk profile, highlight relevant signals, preserve the supporting evidence and make the results easier for a credit analyst or monitoring team to review.

The project brings together complementary perspectives that are commonly used in the monitoring of credit exposures:

- Early Warning Indicators (EWIs) and the information associated with the EWS score;
- internal behavioural performance and available Centrale dei Rischi (CR) information;
- financial-statement analysis;
- debt-service capacity and financial sustainability.

The output is a structured assessment by macro-area, supported by indicator-level evidence, deterministic comments, an overall status and an executive narrative. It is intended to support the monitoring process and the prioritisation of analytical attention. It does not replace the responsible credit function, the analyst's judgement or the institution's formal credit processes.

## Monitoring dimensions

### 1. Early Warning Indicators and EWS score

Early Warning Indicators are signals that may point to a change in a counterparty's risk profile. In a monitoring process, they help identify developments that warrant attention before a deterioration becomes a realised credit event.

The project supports a rule-based approach to the evaluation of configured indicators: each implemented rule evaluates its input against explicit conditions and thresholds and produces a structured outcome. The Customer Profile data contract also accommodates EWS-related context, including score class, notching, score variation and active EWIs.

An important distinction must be maintained between:
- **rule-based EWI evidence**, where a configured and implemented rule is evaluated by the deterministic engine;
- **EWS score context**, where externally supplied score information is represented as descriptive information.

The project does not claim to calculate or recalibrate an originating institution's EWS score unless a specific calculation is implemented as a deterministic rule. A score or active-EWI value supplied as context is not, by itself, recomputed by the application.

### 2. Internal behavioural performance

Behavioural monitoring considers information arising from the existing credit relationship, such as the evolution of exposures, utilisation, repayment behaviour and other available internal signals. In the project, behavioural checks are represented through the Behavioural Analysis domain and its configured deterministic rule evidence.

The analysis is based on the fields supplied for the assessment run. The current application accepts a structured Excel workbook; it does not directly connect to core banking systems or automatically retrieve a time series of account movements. Therefore, longitudinal monitoring depends on the data made available in the input and should not be confused with an already implemented persistent historical-monitoring platform.

### 3. Centrale dei Rischi

Centrale dei Rischi information provides an external-system view of a counterparty's credit exposures and their composition. It can complement internal behavioural information by adding visibility over the broader banking system.

The current implementation supports a limited descriptive CR exposure snapshot in Behavioural Analysis: a reference date, total utilised exposure at system level and a breakdown into revocable, term and self-liquidating facilities. The application can display these values and, when all components are available, highlight a reconciliation difference.

**Current implementation boundary:** these CR figures are contextual information supplied in the workbook. They are not fetched directly from Banca d'Italia, are not a complete ingestion of the CR report, and do not currently feed the behavioural rule calculations or alter the deterministic assessment status. More advanced CR analytics—such as monthly trend analysis, bank-by-bank concentration, past-due classifications, returned/overdrawn positions or system-wide deterioration patterns—should be described as potential extensions unless and until implemented.

### 4. Financial-statement analysis

Financial Analysis evaluates configured indicators derived from the counterparty's financial information. It provides a structured way to identify weaknesses or changes in economic performance, balance-sheet structure and financial equilibrium.

The project evaluates the rules implemented in the Financial Analysis domain and preserves the observed values, thresholds, severity and explanatory evidence where available. The exact indicator catalogue and calculation logic are defined by the current configuration and source code, rather than duplicated in this document.

### 5. Debt sustainability

Debt Sustainability complements the financial-statement perspective by focusing on the counterparty's ability to service its financial obligations. The domain evaluates the configured sustainability indicators and contributes its own evidence and status to the overall assessment.

The project treats this as a distinct analytical dimension: a counterparty's balance-sheet or income-statement position and its capacity to meet debt-service commitments are related, but they are not interchangeable concepts.

## How the automated support works

The workflow follows a controlled sequence:

```text
Structured counterparty information
              ↓
       Input validation
              ↓
  Deterministic domain rule checks
              ↓
 EWI / behavioural / financial /
   debt-sustainability evidence
              ↓
       Macro-area results
              ↓
   Overall assessment and rationale
              ↓
     Structured case analysis
              ↓
     Executive reporting output
```

The deterministic engine is the authoritative source for configured rule outcomes, severity, macro-area status and final assessment status. Each rule result distinguishes between `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE`; unavailable evidence must not be interpreted as a normal observation.

The optional AI component operates only after the deterministic assessment. It can help express the structured evidence in a readable narrative, but it cannot create rule outcomes, change severities or modify the final status. A deterministic reporting fallback is available when the selected provider fails or returns invalid output.

## What the project is—and is not

| The project is | The project is not |
|---|---|
| A prototype for automated credit-quality monitoring support | An autonomous credit-granting or credit-rejection system |
| A framework for evaluating configured EWIs and domain-specific risk rules | A replacement for the bank's official EWS platform or score-calibration process |
| A way to bring behavioural, CR, financial and debt-sustainability evidence into a structured case view | A direct integration with core banking systems or Banca d'Italia CR services |
| A decision-support aid for analysts and monitoring teams | A substitute for professional judgement, governance or formal credit procedures |
| A deterministic and traceable assessment followed by optional AI-assisted reporting | An LLM-driven credit decision engine |

## Current prototype limitations and extension opportunities

The current Streamlit workflow uses Excel Upload as its input source and processes the selected scenario as an assessment run. It does not yet provide continuous scheduled monitoring, automatic source-system ingestion, persistent counterparty history or a longitudinal dashboard across successive runs.

These are natural extension areas for a production-oriented monitoring platform:

- automated ingestion and reconciliation of internal credit data and CR extracts;
- storage of dated observations and comparison across monitoring periods;
- trend and variation analysis for EWI, EWS score, behavioural and financial indicators;
- richer CR analysis, including exposure composition, concentration and deterioration signals;
- alerts, work queues and follow-up tracking for monitoring teams;
- model governance, rule-set versioning and a persistent audit trail.

These items are possible future developments, not claims about the current implementation.

## Related technical documentation

- [Architecture](architecture.md) — deterministic assessment, domain boundaries and reporting.
- [Customer Profile](customer-profile.md) — EWS score fields, active EWIs and contextual profile data.
- [Behavioural Analysis](behavioural-analysis.md) — behavioural rule evidence and the current CR exposure context.
- [Application Workflow](application-workflow.md) — Excel input, execution sequence and results presentation.
- [Rules](rules.md) — configuration, deterministic implementation and rule lifecycle.
