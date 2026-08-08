from dataclasses import dataclass

# CreditPosition represents the input data used by the assessment engine.
# It should contain business and financial data, but no rule-evaluation logic.
# Rules read the position and independently determine whether their conditions are triggered.

@dataclass
class CreditPosition:
    position_id: str
    revenue_growth: float
    ebitda: float
    profit_loss: float
    ebitda_margin: float
    pfn_to_ebitda: float
    interest_expense: float