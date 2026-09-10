from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviouralData:
    """Synthetic banking-behaviour inputs used by behavioural assessment rules.

    Ratios are represented as decimals (for example, 0.90 means 90%).
    Missing values are represented by None and remain explicitly not evaluable.
    """

    average_utilization: float | None = None
    overdraft_days: float | None = None
    payment_delay_days: float | None = None
    exposure_growth: float | None = None
