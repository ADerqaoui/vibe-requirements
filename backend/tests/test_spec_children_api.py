"""Spec child persistence API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec


def seed_spec_tree(db_session: Session) -> tuple[int, int, int]:
    """Seed parent, child, and grandchild Specs."""
    Model.__table__
    Prompt.__table__
    project = Project(name="Demo")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    parent = Spec(need_id=need.id, layer_id=layer.id, text="Parent", source="ai")
    sibling = Spec(need_id=need.id, layer_id=layer.id, text="Sibling", source="ai")
    db_session.add_all([parent, sibling])
    db_session.flush()
    child = Spec(
        need_id=need.id,
        parent_spec_id=parent.id,
        layer_id=layer.id,
        text="Child",
        source="ai",
    )
    db_session.add(child)
    db_session.flush()
    grandchild = Spec(
        need_id=need.id,
        parent_spec_id=child.id,
        layer_id=layer.id,
        text="Grandchild",
        source="ai",
    )
    db_session.add(grandchild)
    db_session.flush()
    parent_id = parent.id
    child_id = child.id
    sibling_id = sibling.id
    db_session.commit()
    return parent_id, child_id, sibling_id


@pytest.mark.asyncio
async def test_spec_children_api_creates_pending_child(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """A child Spec can be accepted under a parent Spec."""
    parent_id, _child_id, _sibling_id = seed_spec_tree(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/specs/{parent_id}/specs",
            json={"statement": "New child"},
        )

    assert response.status_code == 201
    assert response.json()["statement"] == "New child"
    created_spec = db_session.get(Spec, response.json()["id"])
    assert created_spec is not None
    assert created_spec.parent_spec_id == parent_id
    assert created_spec.status == "pending"


@pytest.mark.asyncio
async def test_spec_children_api_missing_parent_and_blank_statement(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Child Spec API returns 404 for missing parent and 422 for blank statements."""
    parent_id, _child_id, _sibling_id = seed_spec_tree(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_create = await client.post("/api/specs/999/specs", json={"statement": "Spec"})
        missing_list = await client.get("/api/specs/999/specs")
        blank_create = await client.post(
            f"/api/specs/{parent_id}/specs",
            json={"statement": "   "},
        )

    assert missing_create.status_code == 404
    assert missing_list.status_code == 404
    assert blank_create.status_code == 422


@pytest.mark.asyncio
async def test_spec_children_api_lists_direct_children_only(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """GET child Specs excludes siblings and grandchildren."""
    parent_id, _child_id, _sibling_id = seed_spec_tree(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/specs/{parent_id}/specs")

    assert response.status_code == 200
    assert [item["statement"] for item in response.json()] == ["Child"]
