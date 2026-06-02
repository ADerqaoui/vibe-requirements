"""Cost summary API schemas."""
from pydantic import BaseModel


class CostProviderSummary(BaseModel):
    """Monthly spend grouped by provider."""

    provider: str
    month_sek: float


class CostModelSummary(BaseModel):
    """Monthly spend grouped by model."""

    model_id: int
    model_name: str
    month_sek: float


class CostSummary(BaseModel):
    """Read-only cost dashboard response."""

    currency: str
    ceiling_sek: float
    month_spent_sek: float
    month_remaining_sek: float
    all_time_spent_sek: float
    by_provider: list[CostProviderSummary]
    by_model: list[CostModelSummary]
