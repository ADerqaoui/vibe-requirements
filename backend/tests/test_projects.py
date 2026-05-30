"""Project API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.orm import Session


@pytest.mark.asyncio
async def test_project_crud_endpoints(api_app: FastAPI) -> None:
    """Create, list, get, rename, and delete a project."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post("/api/projects", json={"name": "Alpha"})
        project = create_response.json()
        duplicate_response = await client.post("/api/projects", json={"name": "Alpha"})
        list_response = await client.get("/api/projects")
        detail_response = await client.get(f"/api/projects/{project['id']}")
        rename_response = await client.patch(f"/api/projects/{project['id']}", json={"name": "Beta"})
        delete_response = await client.delete(f"/api/projects/{project['id']}")
        missing_response = await client.get(f"/api/projects/{project['id']}")

    assert create_response.status_code == 201
    assert project["name"] == "Alpha"
    assert duplicate_response.status_code == 409
    assert list_response.status_code == 200
    assert [item["name"] for item in list_response.json()] == ["Alpha"]
    assert detail_response.status_code == 200
    assert detail_response.json()["needs"] == []
    assert rename_response.status_code == 200
    assert rename_response.json()["name"] == "Beta"
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_project_delete_cascades_children(api_app: FastAPI, db_session: Session) -> None:
    """Deleting a project cascades future child rows at the database level."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post("/api/projects", json={"name": "Cascade"})
        project_id = create_response.json()["id"]

    db_session.execute(
        text("INSERT INTO needs (project_id, statement) VALUES (:project_id, :statement)"),
        {"project_id": project_id, "statement": "Need one"},
    )
    db_session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        delete_response = await client.delete(f"/api/projects/{project_id}")

    assert delete_response.status_code == 204

    need_count = db_session.scalar(text("SELECT COUNT(*) FROM needs"))
    assert need_count == 0
