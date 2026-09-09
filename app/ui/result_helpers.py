from typing import Any


def get_llm_model_from_result(result: Any) -> str | None:
    """Retrieve the configured LLM model from the workflow result."""
    return getattr(result, "llm_model", None)


def resolve_report_badge(
    selected_reporting_mode: str,
    generator_used: str | None,
    configured_model: str | None,
) -> tuple[str, str]:
    """Resolve the badge for the actual Executive Report generator."""
    if generator_used == "FALLBACK":
        return "fallback", "Deterministic fallback"

    if generator_used == "PRIMARY":
        if selected_reporting_mode == "Gemini + Fallback":
            return "ai", "AI-generated — Gemini"
        if selected_reporting_mode == "Ollama + Fallback":
            return "ai", "AI-generated — Local LLM"

    return "det", "Deterministic — Rule Engine"


def _status_kind(status: str) -> str:
    """Map assessment status to the existing badge categories."""
    if status in {"CRITICAL", "HIGH_RISK", "HIGH RISK"}:
        return "fallback"
    if status in {"WARNING", "MEDIUM_RISK", "MEDIUM RISK"}:
        return "fallback"
    return "det"


def _rule_status_counts(result: Any) -> dict[str, int]:
    """Count actual RuleResult statuses without applying business logic."""
    counts = {
        "TRIGGERED": 0,
        "NOT_TRIGGERED": 0,
        "NOT_EVALUABLE": 0,
    }

    assessment = getattr(result, "assessment", None)
    for rule_result in getattr(assessment, "rule_results", []) or []:
        status = getattr(getattr(rule_result, "status", None), "value", "")
        if status in counts:
            counts[status] += 1

    return counts
