"""Spec API schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SpecCreate(BaseModel):
    """Request body for accepting a generated spec."""

    statement: str = Field(min_length=1)

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
    statement: str
    complexity: int | None
    status: str
    created_at: str
    updated_at: str


class SpecTreeNode(BaseModel):
    """Nested Spec tree node response body."""

    id: int
    statement: str
    complexity: int | None
    status: str
    parent_spec_id: int | None
    children: list["SpecTreeNode"]
