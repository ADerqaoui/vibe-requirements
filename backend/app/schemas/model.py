"""Model registry API schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator

MODEL_PROVIDERS = {"ollama", "anthropic", "openai", "deepseek"}
MODEL_TIERS = {"low", "mid", "high"}


def normalize_optional_text(value: str | None) -> str | None:
    """Trim optional text and store blanks as null."""
    if value is None:
        return None
    normalized_value = value.strip()
    if normalized_value == "":
        return None
    return normalized_value


def normalize_required_text(value: str) -> str:
    """Trim required text and reject blanks."""
    normalized_value = value.strip()
    if normalized_value == "":
        raise ValueError("Value must not be blank")
    return normalized_value


class ModelCreate(BaseModel):
    """Request body for creating a model."""

    provider: str
    name: str
    ollama_tag: str | None = None
    api_model_id: str | None = None
    tier: str
    input_cost_per_1k: float = Field(default=0, ge=0)
    output_cost_per_1k: float = Field(default=0, ge=0)
    enabled: bool = True

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        """Normalize and validate provider."""
        normalized_value = normalize_required_text(value)
        if normalized_value not in MODEL_PROVIDERS:
            raise ValueError("Unknown model provider")
        return normalized_value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Normalize model name."""
        return normalize_required_text(value)

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, value: str) -> str:
        """Normalize and validate tier."""
        normalized_value = normalize_required_text(value)
        if normalized_value not in MODEL_TIERS:
            raise ValueError("Unknown model tier")
        return normalized_value

    @field_validator("ollama_tag", "api_model_id")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        """Normalize optional identifiers."""
        return normalize_optional_text(value)


class ModelUpdate(BaseModel):
    """Request body for editing a model."""

    provider: str | None = None
    name: str | None = None
    ollama_tag: str | None = None
    api_model_id: str | None = None
    tier: str | None = None
    input_cost_per_1k: float | None = Field(default=None, ge=0)
    output_cost_per_1k: float | None = Field(default=None, ge=0)
    enabled: bool | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        """Normalize and validate provider when provided."""
        if value is None:
            return None
        normalized_value = normalize_required_text(value)
        if normalized_value not in MODEL_PROVIDERS:
            raise ValueError("Unknown model provider")
        return normalized_value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        """Normalize model name when provided."""
        if value is None:
            return None
        return normalize_required_text(value)

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, value: str | None) -> str | None:
        """Normalize and validate tier when provided."""
        if value is None:
            return None
        normalized_value = normalize_required_text(value)
        if normalized_value not in MODEL_TIERS:
            raise ValueError("Unknown model tier")
        return normalized_value

    @field_validator("ollama_tag", "api_model_id")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        """Normalize optional identifiers."""
        return normalize_optional_text(value)


class ModelRead(BaseModel):
    """Model response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    name: str
    ollama_tag: str | None
    api_model_id: str | None
    tier: str
    input_cost_per_1k: float
    output_cost_per_1k: float
    enabled: bool
    cumulative_cost_sek: float
