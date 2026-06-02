"""Prompt registry API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.seed.prompts_seed import DEFAULT_PROMPT_ROWS
from app.seed.run import seed_prompts


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_prompts_api_returns_seeded_active_prompts(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Prompts endpoint returns active seeded prompts in stable order."""
    seed_prompts(db_session)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/prompts")

    assert response.status_code == 200
    body = response.json()
    expected = sorted(DEFAULT_PROMPT_ROWS, key=lambda row: row["task"])
    assert [item["task"] for item in body] == [item["task"] for item in expected]
    assert [item["version"] for item in body] == [1, 1, 1, 1]
    assert [item["template"] for item in body] == [item["template"] for item in expected]
    assert all(item["layer_id"] is None for item in body)
    assert all(item["discipline_scope"] is None for item in body)
