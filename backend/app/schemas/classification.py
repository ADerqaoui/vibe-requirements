"""Classification API schemas."""
from pydantic import BaseModel, Field


class ClassificationVote(BaseModel):
    """One model's parsed complexity vote."""

    model_id: int
    vote: int = Field(ge=1, le=5)


class ClassificationResult(BaseModel):
    """Spec complexity classification result."""

    spec_id: int
    votes: list[ClassificationVote]
    complexity: int = Field(ge=1, le=5)
