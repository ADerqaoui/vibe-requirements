"""Inspection API schemas."""
from pydantic import BaseModel, Field


class InspectRequest(BaseModel):
    """Request body for running a Spec inspection."""

    model_id: int | None = None


class InspectionCriterion(BaseModel):
    """One parsed inspection criterion."""

    name: str
    verdict: str
    note: str


class InspectionFindings(BaseModel):
    """Parsed inspection findings."""

    criteria: list[InspectionCriterion]
    summary: str | None = None


class SpecInspectionOut(BaseModel):
    """Persisted inspection response."""

    id: int
    spec_id: int
    model_id: int
    selected_model_id: int | None = None
    selected_model_name: str | None = None
    findings: InspectionFindings
    summary: str | None = None
    passes: int = Field(ge=1)
    created_at: str
