"""Spec API schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SpecCreate(BaseModel):
    """Request body for accepting a generated spec."""

    statement: str = Field(min_length=1)
    target_layer_id: int | None = None

    @field_validator("statement")
    @classmethod
    def normalize_statement(cls, value: str) -> str:
        """Trim and reject blank statements."""
        normalized_value = value.strip()
        if normalized_value == "":
            raise ValueError("Spec statement must not be blank")
        return normalized_value


class ManualSpecCreate(BaseModel):
    """Request body for manually authoring a spec."""

    text: str = Field(min_length=1)
    target_layer_id: int | None = None

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Trim and reject blank text."""
        normalized_value = value.strip()
        if normalized_value == "":
            raise ValueError("Spec text must not be blank")
        return normalized_value


class SpecOut(BaseModel):
    """Spec response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    need_id: int
    parent_spec_id: int | None
    layer_id: int
    layer_name: str
    req_id: str | None
    statement: str
    source: str
    complexity: int | None
    status: str
    latest_inspection_id: int | None = None
    created_at: str
    updated_at: str


class SpecTreeNode(BaseModel):
    """Nested Spec tree node response body."""

    id: int
    req_id: str | None
    statement: str
    source: str
    complexity: int | None
    status: str
    parent_spec_id: int | None
    layer_id: int
    layer_name: str
    latest_inspection_id: int | None = None
    children: list["SpecTreeNode"]


class SpecUpdate(BaseModel):
    """Request body for text-only spec edits."""

    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Trim and reject blank text."""
        normalized_value = value.strip()
        if normalized_value == "":
            raise ValueError("Spec text must not be blank")
        return normalized_value


class SpecRevisionOut(BaseModel):
    """Spec revision history response body."""

    model_config = ConfigDict(from_attributes=True)

    revision_number: int
    text: str
    status: str
    source: str
    change_type: str
    created_at: str
