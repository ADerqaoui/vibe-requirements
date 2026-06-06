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
    layer_name: str | None = None
    discipline_scope: str | None
    template: str
    updated_at: str


class PromptVersionCreate(BaseModel):
    """Create a new immutable prompt version."""

    template: str
    layer_id: int | None = None
    name: str | None = None
    description: str | None = None


class PromptVersionRead(PromptRead):
    """Prompt version history response."""

    id: int
    enabled: int
    created_at: str


class PromptVariantRead(BaseModel):
    """Enabled prompt variant response."""

    name: str
    version: int
    template: str
    is_default: bool
    prompt_id: int
    layer_id: int | None
    layer_name: str | None = None
    scope_label: str


class PromptDefaultSet(BaseModel):
    """Set a task/layer default variant."""

    task: str
    layer_id: int | None = None
    name: str


class PromptPreviewRequest(BaseModel):
    """Run a draft prompt template through a model."""

    task: str
    template: str
    variables: dict[str, object]
    model_id: int | None = None


class PromptPreviewResponse(BaseModel):
    """Prompt preview response."""

    rendered_prompt: str
    output: str
    model_id: int
    model_name: str
    cost_sek: float
