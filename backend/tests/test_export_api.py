"""Project export API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.models.project import Project


@pytest.mark.asyncio
async def test_export_api_attachment_headers(api_app: FastAPI, db_session: Session) -> None:
    """Export API returns Markdown with attachment filename."""
    project = Project(name="Brake Controller")
    db_session.add(project)
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/projects/{project.id}/export.md")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["content-disposition"] == 'attachment; filename="brake-controller.md"'
    assert response.text.startswith("# Brake Controller\n")


@pytest.mark.asyncio
async def test_export_api_inline_omits_attachment_header(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Inline export returns the same Markdown body without attachment disposition."""
    project = Project(name="Inline Project")
    db_session.add(project)
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/projects/{project.id}/export.md?inline=1")

    assert response.status_code == 200
    assert "content-disposition" not in response.headers
    assert response.text.startswith("# Inline Project\n")


@pytest.mark.asyncio
async def test_export_api_missing_project(api_app: FastAPI) -> None:
    """Missing Projects return 404."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/projects/999/export.md")

    assert response.status_code == 404
