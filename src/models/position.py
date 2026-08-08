from dataclasses import dataclass


@dataclass
class CreditPosition:
    position_id: str
    revenue_growth: float
    ebitda: float
    profit_loss: float
    ebitda_margin: float
    pfn_to_ebitda: float
    interest_expense: float