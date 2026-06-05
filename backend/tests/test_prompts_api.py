"""Prompt registry API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.prompt import Prompt
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
    expected_tasks = [row["task"] for row in sorted(DEFAULT_PROMPT_ROWS, key=lambda row: row["task"])]
    assert [item["task"] for item in body] == expected_tasks
    assert [item["version"] for item in body] == [1, 1, 2, 1]
    assert body[2]["template"].startswith("Generate child specifications for this parent specification.")
    assert all(item["layer_id"] is None for item in body)
    assert all(item["discipline_scope"] is None for item in body)
    assert all("id" not in item for item in body)


@pytest.mark.asyncio
async def test_prompt_versions_api_lists_newest_first(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Version history includes id and ordering."""
    seed_prompts(db_session)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/prompts/generate_spec_to_child/versions")

    assert response.status_code == 200
    body = response.json()
    assert [item["version"] for item in body] == [2, 1]
    assert body[0]["enabled"] == 1
    assert body[1]["enabled"] == 0
    assert {"id", "created_at", "updated_at", "template"} <= set(body[0])


@pytest.mark.asyncio
async def test_create_prompt_version_api_success(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """POST creates a new active prompt version."""
    seed_prompts(db_session)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/classify_spec/versions",
            json={"template": "Score {spec_statement}", "name": "Score Spec"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["enabled"] == 1
    assert body["name"] == "Score Spec"


@pytest.mark.asyncio
async def test_create_prompt_version_api_rejects_invalid_template(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Invalid templates return the required 422 body."""
    seed_prompts(db_session)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/classify_spec/versions",
            json={"template": "Missing variable"},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "prompt_template_invalid"
    assert "missing variables: spec_statement" in response.json()["reason"]


@pytest.mark.asyncio
async def test_create_prompt_version_api_unknown_task_404(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Unknown task creates return 404."""
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/prompts/missing/versions", json={"template": "{spec_statement}"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_promote_prompt_api_success_and_unknown_404(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Promote endpoint flips active version and rejects unknown ids."""
    seed_prompts(db_session)
    use_db_session(api_app, db_session)
    v1 = db_session.query(Prompt).filter_by(task="generate_spec_to_child", version=1).one()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/prompts/{v1.id}/promote")
        missing_response = await client.post("/api/prompts/999999/promote")

    assert response.status_code == 200
    assert response.json()["version"] == 1
    assert response.json()["enabled"] == 1
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_prompt_variants_api_lists_creates_and_sets_default(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Variant endpoints expose defaults and allow creating new variants."""
    seed_prompts(db_session)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/prompts/classify_spec/versions",
            json={"template": "EARS {spec_statement}", "name": "EARS"},
        )
        variants_response = await client.get("/api/prompts/classify_spec/variants")
        default_response = await client.post(
            "/api/prompts/set-default",
            json={"task": "classify_spec", "layer_id": None, "name": "EARS"},
        )
        after_response = await client.get("/api/prompts/classify_spec/variants")
        missing_response = await client.post(
            "/api/prompts/set-default",
            json={"task": "classify_spec", "layer_id": None, "name": "Missing"},
        )

    assert create_response.status_code == 200
    assert variants_response.status_code == 200
    assert default_response.status_code == 200
    assert missing_response.status_code == 404
    assert {item["name"] for item in variants_response.json()} == {"Classify Spec", "EARS"}
    assert [item for item in after_response.json() if item["is_default"]][0]["name"] == "EARS"
