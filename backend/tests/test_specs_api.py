"""Specs API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.prompt import Prompt
from app.models.project import Project
from app.models.spec import Spec
from app.seed.run import seed_reference_data


def seed_need_with_layer(db_session: Session) -> tuple[int, int]:
    """Seed two Needs and the default Spec layer."""
    Model.__table__
    Prompt.__table__
    seed_reference_data(db_session)
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    other_need = Need(project_id=project.id, statement="Accelerate safely")
    db_session.add_all([need, other_need])
    db_session.flush()
    need_id = need.id
    other_need_id = other_need.id
    db_session.commit()
    return need_id, other_need_id


@pytest.mark.asyncio
async def test_specs_api_creates_and_lists_only_need_specs(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Specs can be accepted under a Need and listed by Need."""
    need_id, other_need_id = seed_need_with_layer(db_session)
    layer_id = db_session.query(Layer).filter(Layer.name == "System Requirement").one().id
    other_spec = Spec(need_id=other_need_id, layer_id=layer_id, text="Other", source="ai")
    db_session.add(other_spec)
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            f"/api/needs/{need_id}/specs",
            json={"statement": "The system shall brake."},
        )
        list_response = await client.get(f"/api/needs/{need_id}/specs")

    assert create_response.status_code == 201
    assert create_response.json()["statement"] == "The system shall brake."
    assert create_response.json()["parent_spec_id"] is None
    assert create_response.json()["layer_name"] == "System Requirement"
    assert create_response.json()["req_id"] == "REQ-SYS-0001"
    assert create_response.json()["source"] == "ai"
    assert [item["statement"] for item in list_response.json()] == ["The system shall brake."]
    assert [item["parent_spec_id"] for item in list_response.json()] == [None]

    created_spec = db_session.get(Spec, create_response.json()["id"])
    assert created_spec is not None
    assert created_spec.status == "pending"
    assert created_spec.layer_id == layer_id


@pytest.mark.asyncio
async def test_spec_tree_includes_layer_badges(api_app: FastAPI, db_session: Session) -> None:
    """Spec tree responses include layer, req_id, and source."""
    need_id, _other_need_id = seed_need_with_layer(db_session)
    layer = db_session.query(Layer).filter_by(name="System Requirement").one()
    spec = Spec(need_id=need_id, layer_id=layer.id, text="Root", source="ai", req_id="REQ-SYS-0001")
    db_session.add(spec)
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/needs/{need_id}/spec-tree")

    assert response.status_code == 200
    assert response.json()[0]["layer_id"] == layer.id
    assert response.json()[0]["layer_name"] == "System Requirement"
    assert response.json()[0]["req_id"] == "REQ-SYS-0001"
    assert response.json()[0]["source"] == "ai"


@pytest.mark.asyncio
async def test_specs_api_edits_text_and_preserves_identity(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """PATCH edits text, flips source, and preserves identity fields."""
    need_id, _other_need_id = seed_need_with_layer(db_session)
    layer = db_session.query(Layer).filter_by(name="System Requirement").one()
    spec = Spec(
        need_id=need_id,
        layer_id=layer.id,
        text="Original",
        source="ai",
        status="accepted",
        req_id="REQ-SYS-0001",
    )
    db_session.add(spec)
    db_session.commit()
    original_updated_at = spec.updated_at

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(f"/api/specs/{spec.id}", json={"text": " Edited text "})

    assert response.status_code == 200
    body = response.json()
    assert body["statement"] == "Edited text"
    assert body["source"] == "manual"
    assert body["req_id"] == "REQ-SYS-0001"
    assert body["layer_id"] == layer.id
    assert body["status"] == "accepted"
    assert body["updated_at"] >= original_updated_at


@pytest.mark.asyncio
async def test_specs_api_edit_rejects_blank_and_missing(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """PATCH returns 422 for blank text and 404 for unknown specs."""
    need_id, _other_need_id = seed_need_with_layer(db_session)
    layer = db_session.query(Layer).filter_by(name="System Requirement").one()
    spec = Spec(need_id=need_id, layer_id=layer.id, text="Original", source="ai", req_id="REQ-SYS-0001")
    db_session.add(spec)
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        blank_response = await client.patch(f"/api/specs/{spec.id}", json={"text": "   "})
        missing_response = await client.patch("/api/specs/999", json={"text": "Edited"})

    assert blank_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_specs_api_missing_need_and_blank_statement(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Specs API returns 404 for missing Need and 422 for blank statements."""
    need_id, _other_need_id = seed_need_with_layer(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_create = await client.post("/api/needs/999/specs", json={"statement": "Spec"})
        missing_list = await client.get("/api/needs/999/specs")
        blank_create = await client.post(f"/api/needs/{need_id}/specs", json={"statement": "   "})

    assert missing_create.status_code == 404
    assert missing_list.status_code == 404
    assert blank_create.status_code == 422
