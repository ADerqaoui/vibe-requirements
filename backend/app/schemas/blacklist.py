"""Blacklist API schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BlacklistCreate(BaseModel):
    """Request body for blacklisting rejected text."""

    statement: str = Field(min_length=1)

    @field_validator("statement")
    @classmethod
    def normalize_statement(cls, value: str) -> str:
        """Trim and reject blank statements."""
        normalized_value = value.strip()
        if normalized_value == "":
            raise ValueError("Blacklist statement must not be blank")
        return normalized_value


class BlacklistEntryOut(BaseModel):
    """Blacklist entry response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_need_id: int | None
    parent_spec_id: int | None
    text: str
    source: str
    created_at: str
