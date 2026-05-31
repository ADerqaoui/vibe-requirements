"""Completion API schemas."""
from pydantic import BaseModel, Field, field_validator


class CompletionRequest(BaseModel):
    """Manual model completion request."""

    prompt: str = Field(min_length=1)
    system: str | None = None

    @field_validator("prompt")
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        """Reject blank prompts after trimming."""
        normalized_value = value.strip()
        if normalized_value == "":
            raise ValueError("Prompt must not be blank")
        return normalized_value

    @field_validator("system")
    @classmethod
    def normalize_system(cls, value: str | None) -> str | None:
        """Store blank system prompts as null."""
        if value is None:
            return None
        normalized_value = value.strip()
        if normalized_value == "":
            return None
        return normalized_value


class CompletionResult(BaseModel):
    """Manual model completion response."""

    text: str
    in_tokens: int
    out_tokens: int
    cost_sek: float
    duration_ms: int
