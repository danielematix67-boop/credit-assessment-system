# ============================================================
# Demo Scenarios
# ============================================================

DEMO_SCENARIOS = {

    # --------------------------------------------------------
    # 1. Healthy
    # --------------------------------------------------------

    "Healthy Company": {
        "description": (
            "A financially healthy company with positive revenue growth, "
            "positive EBITDA and net income, strong EBITDA margin and "
            "moderate leverage. No material warning rules should be triggered."
        ),
        "values": {
            "position_id": "DEMO-HEALTHY-001",

            "revenue_growth": 0.10,
            "ebitda": 1_000_000.0,
            "profit_loss": 400_000.0,
            "ebitda_margin": 0.20,
            "pfn_to_ebitda": 1.5,
        },
    },

    # --------------------------------------------------------
    # 2. Moderate deterioration
    # --------------------------------------------------------

    "Moderate Deterioration": {
        "description": (
            "A company showing simultaneous deterioration in revenue "
            "growth and EBITDA margin, while profitability and leverage "
            "remain relatively controlled. This scenario demonstrates "
            "how multiple warning rules can be triggered at the same time."
        ),
        "values": {
            "position_id": "DEMO-MODERATE-001",

            # Revenue deterioration
            "revenue_growth": -0.12,

            # Still positive
            "ebitda": 500_000.0,
            "profit_loss": 100_000.0,

            # Weak margin
            "ebitda_margin": 0.04,

            # Elevated but not extreme leverage
            "pfn_to_ebitda": 3.5,
        },
    },

    # --------------------------------------------------------
    # 3. Profitability + leverage stress
    # --------------------------------------------------------

    "Profitability and Leverage Stress": {
        "description": (
            "A company affected by simultaneous profitability deterioration "
            "and excessive financial leverage. Revenue remains broadly stable, "
            "allowing the demonstration to isolate multiple financial risk "
            "dimensions."
        ),
        "values": {
            "position_id": "DEMO-STRESS-001",

            # Revenue still acceptable
            "revenue_growth": 0.01,

            # Positive but weak EBITDA
            "ebitda": 200_000.0,

            # Negative net income
            "profit_loss": -80_000.0,

            # Very weak margin
            "ebitda_margin": 0.03,

            # High leverage
            "pfn_to_ebitda": 5.5,
        },
    },

    # --------------------------------------------------------
    # 4. Severe multi-risk
    # --------------------------------------------------------

    "Severe Multi-Risk": {
        "description": (
            "A severely distressed company combining revenue contraction, "
            "negative EBITDA, negative profitability, very weak EBITDA margin "
            "and excessive leverage. This scenario is designed to activate "
            "several deterministic rules simultaneously."
        ),
        "values": {
            "position_id": "DEMO-MULTI-RISK-001",

            # Severe revenue contraction
            "revenue_growth": -0.25,

            # Negative EBITDA
            "ebitda": -200_000.0,

            # Negative profitability
            "profit_loss": -300_000.0,

            # Negative EBITDA margin
            "ebitda_margin": -0.10,

            # Very high leverage
            "pfn_to_ebitda": 8.0,
        },
    },

    # --------------------------------------------------------
    # 5. Mixed risk profile
    # --------------------------------------------------------

    "Mixed Risk Profile": {
        "description": (
            "A company with strong revenue growth but simultaneously weak "
            "profitability and excessive leverage. This scenario demonstrates "
            "that a positive indicator does not offset independent rule "
            "violations in other financial dimensions."
        ),
        "values": {
            "position_id": "DEMO-MIXED-001",

            # Strong revenue growth
            "revenue_growth": 0.15,

            # Positive EBITDA
            "ebitda": 300_000.0,

            # Negative net income
            "profit_loss": -50_000.0,

            # Weak margin
            "ebitda_margin": 0.035,

            # Excessive leverage
            "pfn_to_ebitda": 6.5,
        },
    },

    # --------------------------------------------------------
    # 6. Missing information
    # --------------------------------------------------------

    "Missing Information": {
        "description": (
            "A company with incomplete financial information. Several "
            "indicators are unavailable, demonstrating NOT_EVALUABLE "
            "handling and the distinction between financial deterioration "
            "and insufficient information."
        ),
        "values": {
            "position_id": "DEMO-MISSING-001",

            "revenue_growth": -0.05,

            "ebitda": None,
            "profit_loss": None,
            "ebitda_margin": None,
            "pfn_to_ebitda": None,
        },
    },
}
