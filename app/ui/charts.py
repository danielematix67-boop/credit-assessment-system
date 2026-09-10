"""Backward-compatible exports for the Results UI.

The result visualizations now live in the ``app.ui.results`` package. This
module remains as a small compatibility layer so existing imports do not break.
"""

from app.ui.results.dashboard import render_risk_indicator_dashboard
from app.ui.results.decision_bridge import render_decision_path
from app.ui.results.evidence import render_rule_evidence_matrix
from app.ui.results.rule_detail import render_rule_indicator_detail

__all__ = [
    "render_decision_path",
    "render_risk_indicator_dashboard",
    "render_rule_evidence_matrix",
    "render_rule_indicator_detail",
]
