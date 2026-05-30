"""Settings API schemas."""
from pydantic import BaseModel, Field, field_validator

PROVIDER_KEY_NAMES = {
    "anthropic_api_key",
    "openai_api_key",
    "deepseek_api_key",
}


class SettingRead(BaseModel):
    """Setting response body."""

    key: str
    value: str | None


class SettingsRead(BaseModel):
    """Settings API response body."""

    settings: list[SettingRead]
    provider_keys: dict[str, str]


class SettingsUpdate(BaseModel):
    """Request body for updating settings."""

    settings: list[SettingRead] = Field(default_factory=list)

    @field_validator("settings")
    @classmethod
    def reject_secret_settings(cls, value: list[SettingRead]) -> list[SettingRead]:
        """Reject attempts to persist provider key values."""
        for setting in value:
            if setting.key in PROVIDER_KEY_NAMES:
                raise ValueError("Provider API keys are configured through .env only")
        return value
