from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExecutionMetadata:
    """Immutable provenance and timing metadata for one workflow execution."""

    execution_id: str
    started_at: datetime
    reporting_mode: str
    generator_used: str | None
    fallback_used: bool
    error_category: str | None
    assessment_elapsed_time: float
    analysis_elapsed_time: float
    reporting_elapsed_time: float
    total_elapsed_time: float
