"""Project export API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection


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


@pytest.mark.asyncio
async def test_export_api_include_inspections_toggle(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Export API defaults to inspections and can suppress them."""
    project = Project(name="Inspected")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid")
    db_session.add_all([project, layer, model])
    db_session.flush()
    need = Need(project_id=project.id, statement="Need")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Spec", source="ai", req_id="REQ-SYS-0001")
    db_session.add(spec)
    db_session.flush()
    db_session.add(
        SpecInspection(
            spec_id=spec.id,
            model_id=model.id,
            findings='{"criteria":[{"name":"Clarity","verdict":"PASS","note":"clear"}],"summary":"Looks good"}',
            summary="Looks good",
            created_at="2026-06-05T12:00:00",
        )
    )
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        default_response = await client.get(f"/api/projects/{project.id}/export.md")
        disabled_response = await client.get(f"/api/projects/{project.id}/export.md?include_inspections=false")

    assert "Inspection (qwen, 2026-06-05):" in default_response.text
    assert "Inspection (" not in disabled_response.text
