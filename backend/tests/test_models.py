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
    expected_model_rows = {
        (row["provider"], row["name"], row["tier"], row["enabled"])
        for row in MODEL_SEED_ROWS
    }

    assert len(model_rows) == len(MODEL_SEED_ROWS)
    assert set(model_rows) == expected_model_rows
    assert {row[0] for row in model_rows} == {"ollama", "anthropic", "openai", "deepseek"}
    assert {row[0] for row in setting_rows}.issuperset(CORE_SETTINGS)
    for provider, _name, _tier, enabled in model_rows:
        if provider == "ollama":
            assert enabled == 1
        else:
            assert enabled == 0


def test_seed_models_preserves_user_edits(db_session: Session) -> None:
    """Re-running seed does not clobber user-managed model fields."""
    seed_models_and_settings(db_session)
    db_session.execute(
        text(
            """
            UPDATE models
            SET api_model_id = 'claude-actual',
                input_cost_per_1k = 3.0,
                output_cost_per_1k = 15.0,
                enabled = 1
            WHERE provider = 'anthropic' AND name = 'claude'
            """
        )
    )
    db_session.commit()

    seed_models_and_settings(db_session)

    model_row = db_session.execute(
        text(
            """
            SELECT api_model_id, input_cost_per_1k, output_cost_per_1k, enabled
            FROM models
            WHERE provider = 'anthropic' AND name = 'claude'
            """
        )
    ).one()
    assert model_row == ("claude-actual", 3.0, 15.0, 1)


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


@pytest.mark.asyncio
async def test_delete_model_with_call_history_returns_conflict(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Models with historical call logs cannot be hard-deleted."""
    seed_models_and_settings(db_session)
    model_id = db_session.execute(
        text("SELECT id FROM models WHERE provider = 'ollama' ORDER BY id LIMIT 1")
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO call_logs (task, provider, model_id, cost_sek, status)
            VALUES ('test', 'ollama', :model_id, 1.0, 'success')
            """
        ),
        {"model_id": model_id},
    )
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/models/{model_id}")

    model_still_exists = db_session.execute(
        text("SELECT COUNT(*) FROM models WHERE id = :model_id"),
        {"model_id": model_id},
    ).scalar_one()
    assert response.status_code == 409
    assert response.json()["detail"] == "model has call history; disable it instead"
    assert model_still_exists == 1
