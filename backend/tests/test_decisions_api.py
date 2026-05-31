"""Spec decision API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec


def seed_spec(db_session: Session) -> int:
    """Seed one pending Spec."""
    project_count = db_session.scalar(select(func.count()).select_from(Project)) or 0
    project = Project(name=f"Demo {project_count + 1}")
    layer = db_session.scalar(select(Layer).where(Layer.name == "System Requirement"))
    if layer is None:
        layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
        db_session.add(layer)
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="The system shall brake.", source="ai")
    db_session.add(spec)
    db_session.flush()
    spec_id = spec.id
    db_session.commit()
    return spec_id


@pytest.mark.asyncio
async def test_decision_api_accepts_and_rejects(api_app: FastAPI, db_session: Session) -> None:
    """Decision API transitions pending Specs to accepted and rejected."""
    accept_spec_id = seed_spec(db_session)
    reject_spec_id = seed_spec(db_session)
    transport = ASGITransport(app=api_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        accepted = await client.post(
            f"/api/specs/{accept_spec_id}/decision",
            json={"decision": "accepted"},
        )
        rejected = await client.post(
            f"/api/specs/{reject_spec_id}/decision",
            json={"decision": "rejected"},
        )

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert db_session.get(Spec, accept_spec_id).status == "accepted"
    assert db_session.get(Spec, reject_spec_id).status == "rejected"


@pytest.mark.asyncio
async def test_decision_api_is_idempotent_for_same_status(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Applying the same lifecycle decision twice succeeds."""
    spec_id = seed_spec(db_session)
    transport = ASGITransport(app=api_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(f"/api/specs/{spec_id}/decision", json={"decision": "accepted"})
        second = await client.post(f"/api/specs/{spec_id}/decision", json={"decision": "accepted"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_decision_api_rejects_invalid_and_missing_spec(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Decision API rejects pending as settable and returns 404 for missing Specs."""
    spec_id = seed_spec(db_session)
    transport = ASGITransport(app=api_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid = await client.post(f"/api/specs/{spec_id}/decision", json={"decision": "pending"})
        missing = await client.post("/api/specs/999/decision", json={"decision": "accepted"})

    assert invalid.status_code == 422
    assert missing.status_code == 404
