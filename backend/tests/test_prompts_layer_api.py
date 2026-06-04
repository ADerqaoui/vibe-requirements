"""Prompt layer-targeting API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.layer import Layer
from app.models.prompt import Prompt
from app.seed.run import seed_prompts, seed_reference_data


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def layer_id(db_session: Session, name: str) -> int:
    """Return a seeded layer id by name."""
    return db_session.scalar(select(Layer.id).where(Layer.name == name)) or 0


@pytest.mark.asyncio
async def test_create_prompt_version_api_accepts_layer_id(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """POST creates a new active layer-scoped slot without disabling global."""
    seed_reference_data(db_session)
    seed_prompts(db_session)
    use_db_session(api_app, db_session)
    target_layer_id = layer_id(db_session, "System Requirement")

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/classify_spec/versions",
            json={
                "template": "Layer score {spec_statement}",
                "layer_id": target_layer_id,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["layer_id"] == target_layer_id
    assert body["layer_name"] == "System Requirement"
    global_prompt = db_session.scalar(
        select(Prompt).where(
            Prompt.task == "classify_spec",
            Prompt.layer_id.is_(None),
            Prompt.enabled == 1,
        )
    )
    assert global_prompt is not None


@pytest.mark.asyncio
async def test_create_prompt_version_api_rejects_invalid_layers(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """POST rejects unknown layers and the root Need layer."""
    seed_reference_data(db_session)
    seed_prompts(db_session)
    use_db_session(api_app, db_session)
    need_layer_id = layer_id(db_session, "Need")

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unknown = await client.post(
            "/api/prompts/classify_spec/versions",
            json={"template": "Score {spec_statement}", "layer_id": 999999},
        )
        need = await client.post(
            "/api/prompts/classify_spec/versions",
            json={"template": "Score {spec_statement}", "layer_id": need_layer_id},
        )

    assert unknown.status_code == 422
    assert unknown.json()["error"] == "prompt_layer_invalid"
    assert "does not exist" in unknown.json()["reason"]
    assert need.status_code == 422
    assert need.json()["error"] == "prompt_layer_invalid"
    assert "Need layer" in need.json()["reason"]


@pytest.mark.asyncio
async def test_create_prompt_version_api_preserves_existing_layer_metadata(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """POST with layer_id and omitted metadata carries from that layer slot."""
    seed_reference_data(db_session)
    seed_prompts(db_session)
    use_db_session(api_app, db_session)
    target_layer_id = layer_id(db_session, "System Requirement")

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/prompts/classify_spec/versions",
            json={
                "template": "Layer score {spec_statement}",
                "layer_id": target_layer_id,
                "name": "X-specific",
                "description": "Layer-specific description",
            },
        )
        second = await client.post(
            "/api/prompts/classify_spec/versions",
            json={
                "template": "Layer score v2 {spec_statement}",
                "layer_id": target_layer_id,
            },
        )

    assert first.status_code == 200
    assert second.status_code == 200
    body = second.json()
    assert body["name"] == "X-specific"
    assert body["description"] == "Layer-specific description"
