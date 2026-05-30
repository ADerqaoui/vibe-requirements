"""Need API schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_optional_text(value: str | None) -> str | None:
    """Trim optional text and store blanks as null."""
    if value is None:
        return None
    normalized_value = value.strip()
    if normalized_value == "":
        return None
    return normalized_value


def normalize_statement(value: str) -> str:
    """Trim a required statement and reject blank values."""
    normalized_value = value.strip()
    if normalized_value == "":
        raise ValueError("Need statement must not be blank")
    return normalized_value


class NeedCreate(BaseModel):
    """Request body for creating a need."""

    statement: str = Field(min_length=1)
    context: str | None = None
    constraints: str | None = None

    @field_validator("statement")
    @classmethod
    def normalize_statement_field(cls, value: str) -> str:
        """Normalize the statement."""
        return normalize_statement(value)

    @field_validator("context", "constraints")
    @classmethod
    def normalize_optional_text_field(cls, value: str | None) -> str | None:
        """Normalize optional text fields."""
        return normalize_optional_text(value)


class NeedUpdate(BaseModel):
    """Request body for editing a need."""

    statement: str | None = None
    context: str | None = None
    constraints: str | None = None

    @field_validator("statement")
    @classmethod
    def normalize_statement_field(cls, value: str | None) -> str | None:
        """Normalize the statement when provided."""
        if value is None:
            raise ValueError("Need statement must not be null")
        return normalize_statement(value)

    @field_validator("context", "constraints")
    @classmethod
    def normalize_optional_text_field(cls, value: str | None) -> str | None:
        """Normalize optional text fields."""
        return normalize_optional_text(value)

    @model_validator(mode="after")
    def require_one_field(self) -> "NeedUpdate":
        """Require at least one editable field."""
        if not self.model_fields_set:
            raise ValueError("At least one need field must be provided")
        return self


class NeedRead(BaseModel):
    """Need response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    statement: str
    context: str | None
    constraints: str | None
    complexity: int | None
    created_at: str
    updated_at: str
