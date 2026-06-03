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


class SpecOut(BaseModel):
    """Spec response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    need_id: int
    parent_spec_id: int | None
    layer_id: int
    layer_name: str
    statement: str
    complexity: int | None
    status: str
    latest_inspection_id: int | None = None
    created_at: str
    updated_at: str


class SpecTreeNode(BaseModel):
    """Nested Spec tree node response body."""

    id: int
    statement: str
    complexity: int | None
    status: str
    parent_spec_id: int | None
    layer_id: int
    layer_name: str
    latest_inspection_id: int | None = None
    children: list["SpecTreeNode"]
