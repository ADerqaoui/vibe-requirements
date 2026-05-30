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
    assert "anthropic-secret" not in response.text
    assert "deepseek-secret" not in response.text


@pytest.mark.asyncio
async def test_settings_put_updates_non_key_settings_only(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Settings PUT updates values and rejects API-key persistence."""
    seed_models_and_settings(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update_response = await client.put(
            "/api/settings",
            json={
                "settings": [
                    {"key": "fx_rate_usd_sek", "value": "10.5"},
                    {"key": "router_default", "value": "on"},
                ]
            },
        )
        rejected_response = await client.put(
            "/api/settings",
            json={"settings": [{"key": "openai_api_key", "value": "secret"}]},
        )

    db_keys = db_session.execute(text("SELECT key, value FROM settings")).all()
    assert update_response.status_code == 200
    assert {"key": "fx_rate_usd_sek", "value": "10.5"} in update_response.json()["settings"]
    assert {"key": "router_default", "value": "on"} in update_response.json()["settings"]
    assert rejected_response.status_code == 422
    assert ("openai_api_key", "secret") not in db_keys
    assert all(value != "secret" for _key, value in db_keys)
