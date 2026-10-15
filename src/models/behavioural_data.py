from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviouralData:
    """Behavioural rule inputs and contextual latest-Centrale-Rischi exposures.

    Ratios are represented as decimals (for example, 0.90 means 90%).
    Missing values are represented by None and remain explicitly not evaluable.
    CR exposure context is descriptive and does not participate in rule evaluation.
    """

    average_utilization: float | None = None
    overdraft_days: float | None = None
    payment_delay_days: float | None = None
    exposure_growth: float | None = None

    # Latest available Centrale dei Rischi reference month and utilized exposure.
    cr_reference_month: str | None = None
    total_utilized_system: float | None = None
    utilized_revocable: float | None = None
    utilized_term: float | None = None
    utilized_self_liquidating: float | None = None
