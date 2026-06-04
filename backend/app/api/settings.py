"""Settings API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.schemas.setting import SettingsRead, SettingsUpdate
from app.services.router_service import is_router_enabled
from app.services.setting_service import list_settings, update_router_enabled, update_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
async def list_setting_route(db: Session = Depends(get_db)) -> SettingsRead:
    """List DB settings plus masked provider key status."""
    setting_rows, provider_keys = list_settings(db, get_settings())
    return SettingsRead(
        settings=setting_rows,
        provider_keys=provider_keys,
        router_enabled=is_router_enabled(db),
    )


@router.put("", response_model=SettingsRead)
async def update_setting_route(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
) -> SettingsRead:
    """Update non-secret DB settings."""
    update_settings(db, payload.settings)
    if payload.router_enabled is not None:
        update_router_enabled(db, payload.router_enabled)
    setting_rows, provider_keys = list_settings(db, get_settings())
    return SettingsRead(
        settings=setting_rows,
        provider_keys=provider_keys,
        router_enabled=is_router_enabled(db),
    )
