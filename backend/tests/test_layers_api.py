"""Layer API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.seed.run import seed_reference_data


@pytest.mark.asyncio
async def test_layers_api_lists_layers_and_allowed_children(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Layer routes expose ordered layers and allowed child layers."""
    seed_reference_data(db_session)
    system_requirement = db_session.query(Layer).filter_by(name="System Requirement").one()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        layers = await client.get("/api/layers")
        need_children = await client.get("/api/layers/allowed-children?parent_kind=need")
        spec_children = await client.get(
            f"/api/layers/allowed-children?parent_layer_id={system_requirement.id}"
        )

    assert layers.status_code == 200
    assert [item["name"] for item in layers.json()][:2] == ["Need", "System Requirement"]
    assert [item["name"] for item in need_children.json()] == ["System Requirement"]
    assert [item["name"] for item in spec_children.json()] == [
        "System Architecture",
        "SW Requirement",
        "Electronic Requirement",
        "Mechanical Requirement",
    ]


@pytest.mark.asyncio
async def test_layers_api_rejects_bad_allowed_child_selectors(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Allowed-child route validates selector shape and unknown layer ids."""
    seed_reference_data(db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get("/api/layers/allowed-children")
        both = await client.get("/api/layers/allowed-children?parent_kind=need&parent_layer_id=1")
        unknown = await client.get("/api/layers/allowed-children?parent_layer_id=404")

    assert missing.status_code == 400
    assert both.status_code == 400
    assert unknown.status_code == 404
