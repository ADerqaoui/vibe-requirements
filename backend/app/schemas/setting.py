"""Settings API schemas."""
from pydantic import BaseModel, Field, field_validator

ALLOWED_SETTING_KEYS = {
    "fx_rate_usd_sek",
    "complexity_tier_map",
    "router_default",
    "router_enabled",
    "cost_ceiling_sek",
}


class SettingRead(BaseModel):
    """Setting response body."""

    key: str
    value: str | None


class SettingsRead(BaseModel):
    """Settings API response body."""

    settings: list[SettingRead]
    provider_keys: dict[str, str]
    router_enabled: bool = False


class SettingsUpdate(BaseModel):
    """Request body for updating settings."""

    settings: list[SettingRead] = Field(default_factory=list)
    router_enabled: bool | None = None

    @field_validator("settings")
    @classmethod
    def allow_core_settings_only(cls, value: list[SettingRead]) -> list[SettingRead]:
        """Accept only core non-secret settings."""
        for setting in value:
            normalized_key = setting.key.strip()
            if normalized_key not in ALLOWED_SETTING_KEYS:
                raise ValueError("Only core non-secret settings can be updated")
            setting.key = normalized_key
        return value
