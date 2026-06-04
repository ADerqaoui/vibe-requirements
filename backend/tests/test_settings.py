"""Settings API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import settings as settings_api
from app.config import Settings
from app.seed.run import seed_models_and_settings


@pytest.mark.asyncio
async def test_settings_get_masks_provider_key_status(
    api_app: FastAPI,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider key status is presence-only and never exposes values."""
    seed_models_and_settings(db_session)
    monkeypatch.setattr(
        settings_api,
        "get_settings",
        lambda: Settings(
            anthropic_api_key="anthropic-secret",
            openai_api_key="",
            deepseek_api_key="deepseek-secret",
        ),
    )

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/settings")

    body = response.json()
    assert response.status_code == 200
    assert body["provider_keys"] == {
        "anthropic": "configured",
        "openai": "not_configured",
        "deepseek": "configured",
    }
    assert body["router_enabled"] is False
    assert "anthropic-secret" not in response.text
    assert "deepseek-secret" not in response.text


@pytest.mark.asyncio
async def test_settings_put_updates_non_key_settings_only(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Settings PUT updates the four core non-secret settings."""
    seed_models_and_settings(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update_response = await client.put(
            "/api/settings",
            json={
                "settings": [
                    {"key": "fx_rate_usd_sek", "value": "10.5"},
                    {"key": "router_default", "value": "on"},
                    {"key": "complexity_tier_map", "value": "1:low,2-3:mid,4-5:high"},
                    {"key": "cost_ceiling_sek", "value": "75"},
                ],
                "router_enabled": True,
            },
        )

    db_keys = db_session.execute(text("SELECT key, value FROM settings")).all()
    assert update_response.status_code == 200
    assert {"key": "fx_rate_usd_sek", "value": "10.5"} in update_response.json()["settings"]
    assert {"key": "router_default", "value": "on"} in update_response.json()["settings"]
    assert {
        "key": "complexity_tier_map",
        "value": "1:low,2-3:mid,4-5:high",
    } in update_response.json()["settings"]
    assert {"key": "cost_ceiling_sek", "value": "75"} in update_response.json()["settings"]
    assert update_response.json()["router_enabled"] is True
    assert ("fx_rate_usd_sek", "10.5") in db_keys
    assert ("router_default", "on") in db_keys
    assert ("router_enabled", "true") in db_keys


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["OPENAI_API_KEY", "openai_api_key ", "foo"])
async def test_settings_put_rejects_non_core_settings_without_writing(
    api_app: FastAPI,
    db_session: Session,
    key: str,
) -> None:
    """Settings PUT rejects any key outside the four core settings."""
    seed_models_and_settings(db_session)
    before_rows = db_session.execute(text("SELECT key, value FROM settings ORDER BY key")).all()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/settings",
            json={"settings": [{"key": key, "value": "secret"}]},
        )

    after_rows = db_session.execute(text("SELECT key, value FROM settings ORDER BY key")).all()
    assert response.status_code == 422
    assert after_rows == before_rows
    assert all(value != "secret" for _key, value in after_rows)
