"""Model registry API and seed tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.seed.models_seed import CORE_SETTINGS, MODEL_SEED_ROWS
from app.seed.run import seed_models_and_settings


def test_seed_models_and_settings_is_idempotent(db_session: Session) -> None:
    """Model and core setting seed can run repeatedly without duplicates."""
    seed_models_and_settings(db_session)
    seed_models_and_settings(db_session)

    model_rows = db_session.execute(
        text("SELECT provider, name, tier, enabled FROM models ORDER BY id")
    ).all()
    setting_rows = db_session.execute(text("SELECT key, value FROM settings")).all()

    assert len(model_rows) == len(MODEL_SEED_ROWS)
    assert {row[0] for row in model_rows} == {"ollama", "anthropic", "openai", "deepseek"}
    assert {row[0] for row in setting_rows}.issuperset(CORE_SETTINGS)
    for provider, _name, _tier, enabled in model_rows:
        if provider == "ollama":
            assert enabled == 1
        else:
            assert enabled == 0


@pytest.mark.asyncio
async def test_model_crud_and_cumulative_cost(api_app: FastAPI, db_session: Session) -> None:
    """Models can be listed, added, toggled, and removed."""
    seed_models_and_settings(db_session)
    db_session.execute(
        text(
            """
            INSERT INTO call_logs (task, provider, model_id, cost_sek, status)
            VALUES ('test', 'ollama', 1, 12.5, 'success')
            """
        )
    )
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/api/models")
        create_response = await client.post(
            "/api/models",
            json={
                "provider": "openai",
                "name": "Custom GPT",
                "api_model_id": "custom-gpt",
                "tier": "high",
                "input_cost_per_1k": 0.1,
                "output_cost_per_1k": 0.2,
                "enabled": False,
            },
        )
        model_id = create_response.json()["id"]
        enable_response = await client.patch(f"/api/models/{model_id}", json={"enabled": True})
        missing_patch_response = await client.patch("/api/models/999", json={"enabled": False})
        delete_response = await client.delete(f"/api/models/{model_id}")
        missing_delete_response = await client.delete("/api/models/999")

    first_model = list_response.json()[0]
    assert list_response.status_code == 200
    assert first_model["cumulative_cost_sek"] == 12.5
    assert create_response.status_code == 201
    assert create_response.json()["enabled"] is False
    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True
    assert missing_patch_response.status_code == 404
    assert delete_response.status_code == 204
    assert missing_delete_response.status_code == 404
