"""Settings service."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.setting import Setting
from app.schemas.setting import SettingRead

PROVIDERS = ("anthropic", "openai", "deepseek")


def list_settings(db: Session, settings: Settings) -> tuple[list[SettingRead], dict[str, str]]:
    """Return DB settings and masked provider key statuses."""
    setting_rows = db.scalars(select(Setting).order_by(Setting.key)).all()
    provider_keys = {
        provider: _key_status(getattr(settings, f"{provider}_api_key"))
        for provider in PROVIDERS
    }
    return [SettingRead(key=row.key, value=row.value) for row in setting_rows], provider_keys


def update_settings(db: Session, setting_values: list[SettingRead]) -> list[SettingRead]:
    """Upsert non-secret settings."""
    for setting_value in setting_values:
        setting = db.get(Setting, setting_value.key)
        if setting is None:
            db.add(Setting(key=setting_value.key, value=setting_value.value))
            continue
        setting.value = setting_value.value
    db.commit()
    return [SettingRead(key=row.key, value=row.value) for row in db.scalars(select(Setting).order_by(Setting.key))]


def _key_status(value: str) -> str:
    """Return masked key configuration status."""
    if value.strip() == "":
        return "not_configured"
    return "configured"
