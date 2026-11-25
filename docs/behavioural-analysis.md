# Behavioural Analysis: Rule Evidence and Centrale dei Rischi Context

## Purpose

The Behavioural Analysis section combines two distinct information layers:

1. **Deterministic behavioural rule evidence**, evaluated by `BehaviouralAssessmentService`.
2. **Descriptive exposure context** from the latest available Centrale dei Rischi (CR) reference date.

The CR exposure figures are contextual information, not rule inputs. They do not affect rule outcomes, severity, section status, or the final assessment. In the broader credit-quality monitoring scope, these figures complement internal behavioural evidence by providing a limited system-level exposure snapshot; they should not be interpreted as a complete CR analysis or as a longitudinal monitoring series.

## Context data contract

`BehaviouralData` supports the following optional fields:

| Field | Meaning |
|---|---|
| `cr_reference_date` | Reference date of the latest available CR data, represented as ISO date `YYYY-MM-DD` (for example, `2026-09-30`) |
| `total_utilized_system` | Total utilized exposure at system level, in euros |
| `utilized_revocable` | Utilized amount for revocable credit lines, in euros |
| `utilized_term` | Utilized amount for term facilities, in euros |
| `utilized_self_liquidating` | Utilized amount for self-liquidating facilities, in euros |

The values are optional. When exposure amounts are missing, the UI identifies the data as unavailable instead of treating missing values as zero. The input data provider is responsible for supplying the latest available CR reference date; the application does not infer or fetch the CR reference date automatically. The current implementation does not connect directly to Banca d'Italia services and does not automatically retrieve monthly CR records.

## Current scope and limitations

The current CR contract is deliberately narrow: reference date, total utilised system exposure and the three supported facility categories. It does not currently represent the full set of information available in a Centrale dei Rischi report, nor does it implement trend analysis, bank-level concentration analysis, monthly variation monitoring or automated deterioration alerts from CR history. Such analyses are potential extensions and should only be documented as implemented when corresponding input contracts, calculations and tests exist.

## Presentation

In **Detailed Assessment → Behavioural Analysis**, the CR context is displayed before deterministic rule evidence. The UI shows the reference date (displayed as `DD/MM/YYYY`), total utilized system exposure, and its breakdown across revocable, term, and self-liquidating facilities. Where all three components and the total are available, the UI flags a reconciliation difference if the components do not add up to the total.

The full rule evidence remains separate below the contextual figures. Context values do not create rule findings and do not alter the rule catalogue.

## Demo data

The integrated demo scenario uses explicitly synthetic figures for reference date `2026-09-30`:

- Total utilized system exposure: EUR 4,800,000
- Revocable facilities: EUR 1,600,000
- Term facilities: EUR 2,400,000
- Self-liquidating facilities: EUR 800,000

The three categories sum to the synthetic total. These figures are demonstration data, not actual Centrale dei Rischi information.

## Maintenance checklist

- Keep CR context fields optional and descriptive.
- Do not pass CR exposure fields into behavioural rule calculations.
- Keep the reference date explicit; do not assume the current date is the latest CR reference date.
- Update the demo scenario and behavioural service tests when the context contract changes.
