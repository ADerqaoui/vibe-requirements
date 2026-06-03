"""Generation API schemas."""
from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Need-to-Spec generation request."""

    model_id: int
    count: int = Field(ge=1, le=10)
    target_layer_id: int | None = None


class GenerationCandidate(BaseModel):
    """Stateless generated candidate."""

    index: int
    statement: str


class GenerationResult(BaseModel):
    """Need-to-Spec generation result."""

    candidates: list[GenerationCandidate]
