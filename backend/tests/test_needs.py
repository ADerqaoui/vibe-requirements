"""Needs API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.seed.run import seed_reference_data


async def create_project(client: AsyncClient, name: str = "Alpha") -> int:
    """Create a project and return its id."""
    response = await client.post("/api/projects", json={"name": name})
    return int(response.json()["id"])


@pytest.mark.asyncio
async def test_need_crud_endpoints_are_project_scoped(api_app: FastAPI) -> None:
    """Create, list, get, update, and delete a need under a project."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_project(client)
        create_response = await client.post(
            f"/api/projects/{project_id}/needs",
            json={
                "statement": "  Stop the vehicle  ",
                "context": "  wet road  ",
                "constraints": "   ",
            },
        )
        need = create_response.json()
        list_response = await client.get(f"/api/projects/{project_id}/needs")
        detail_response = await client.get(f"/api/needs/{need['id']}")
        update_response = await client.patch(
            f"/api/needs/{need['id']}",
            json={"context": "", "constraints": "under 2 seconds"},
        )
        delete_response = await client.delete(f"/api/needs/{need['id']}")
        missing_response = await client.get(f"/api/needs/{need['id']}")

    assert create_response.status_code == 201
    assert need["statement"] == "Stop the vehicle"
    assert need["context"] == "wet road"
    assert need["constraints"] is None
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [need["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["statement"] == "Stop the vehicle"
    assert update_response.status_code == 200
    assert update_response.json()["context"] is None
    assert update_response.json()["constraints"] == "under 2 seconds"
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_need_project_missing_paths_return_404(api_app: FastAPI) -> None:
    """List and create under a missing project return not found."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/api/projects/999/needs")
        create_response = await client.post(
            "/api/projects/999/needs",
            json={"statement": "Need"},
        )

    assert list_response.status_code == 404
    assert create_response.status_code == 404


@pytest.mark.asyncio
async def test_need_validation_rejects_blank_statement(api_app: FastAPI) -> None:
    """Blank statements are rejected on create and update."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_project(client)
        blank_create_response = await client.post(
            f"/api/projects/{project_id}/needs",
            json={"statement": "   "},
        )
        create_response = await client.post(
            f"/api/projects/{project_id}/needs",
            json={"statement": "Need"},
        )
        blank_update_response = await client.patch(
            f"/api/needs/{create_response.json()['id']}",
            json={"statement": "   "},
        )
        empty_update_response = await client.patch(
            f"/api/needs/{create_response.json()['id']}",
            json={},
        )

    assert blank_create_response.status_code == 422
    assert blank_update_response.status_code == 422
    assert empty_update_response.status_code == 422


@pytest.mark.asyncio
async def test_need_update_clears_complexity_and_bumps_updated_at(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Editing a need clears classification and updates the timestamp."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_project(client)
        create_response = await client.post(
            f"/api/projects/{project_id}/needs",
            json={"statement": "Need"},
        )
        need_id = create_response.json()["id"]

    db_session.execute(
        text("UPDATE needs SET complexity = 3, updated_at = '2000-01-01T00:00:00' WHERE id = :id"),
        {"id": need_id},
    )
    db_session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update_response = await client.patch(
            f"/api/needs/{need_id}",
            json={"statement": "Updated need"},
        )
        missing_update_response = await client.patch(
            "/api/needs/999",
            json={"statement": "Missing"},
        )
        missing_delete_response = await client.delete("/api/needs/999")

    updated_need = update_response.json()
    assert update_response.status_code == 200
    assert updated_need["complexity"] is None
    assert updated_need["updated_at"] != "2000-01-01T00:00:00"
    assert missing_update_response.status_code == 404
    assert missing_delete_response.status_code == 404


@pytest.mark.asyncio
async def test_need_delete_cascades_specs_and_blacklist(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Deleting a need removes descendant specs and need blacklist rows."""
    seed_reference_data(db_session)
    layer_id = db_session.scalar(text("SELECT id FROM layers WHERE name = 'System Requirement'"))
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_project(client)
        create_response = await client.post(
            f"/api/projects/{project_id}/needs",
            json={"statement": "Need"},
        )
        need_id = create_response.json()["id"]

    db_session.execute(
        text("INSERT INTO specs (need_id, layer_id, text) VALUES (:need_id, :layer_id, 'Spec')"),
        {"need_id": need_id, "layer_id": layer_id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO blacklist_entries (parent_need_id, text, source)
            VALUES (:need_id, 'Rejected', 'rejected')
            """
        ),
        {"need_id": need_id},
    )
    db_session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        delete_response = await client.delete(f"/api/needs/{need_id}")

    spec_count = db_session.scalar(text("SELECT COUNT(*) FROM specs"))
    blacklist_count = db_session.scalar(text("SELECT COUNT(*) FROM blacklist_entries"))
    assert delete_response.status_code == 204
    assert spec_count == 0
    assert blacklist_count == 0
