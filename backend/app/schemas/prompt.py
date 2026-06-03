"""Prompt registry API schemas."""
from pydantic import BaseModel, ConfigDict


class PromptRead(BaseModel):
    """Read-only active prompt response."""

    model_config = ConfigDict(from_attributes=True)

    task: str
    name: str
    description: str | None
    version: int
    layer_id: int | None
    discipline_scope: str | None
    template: str
    updated_at: str


class PromptVersionCreate(BaseModel):
    """Create a new immutable prompt version."""

    template: str
    name: str | None = None
    description: str | None = None


class PromptVersionRead(PromptRead):
    """Prompt version history response."""

    id: int
    enabled: int
    created_at: str
