from dataclasses import dataclass


@dataclass
class CreditPosition:
    position_id: str
    revenue_growth: float
    ebitda: float
    profit_loss: float