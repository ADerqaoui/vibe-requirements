"""Inspection API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayError, GatewayResult
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection


class FakeGateway:
    """API fake gateway."""

    def __init__(self, outcome: GatewayResult | GatewayError):
        self.outcome = outcome

    async def health_check(self, timeout_seconds: float) -> None:
        """Always healthy."""

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Return or raise the configured outcome."""
        if isinstance(self.outcome, GatewayError):
            raise self.outcome
        return self.outcome


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def seed_spec_and_model(db_session: Session, enabled: int = 1) -> tuple[int, int]:
    """Seed one Spec and one model."""
    project = Project(name="Demo")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="The system shall brake.", source="ai")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=enabled)
    db_session.add_all([spec, model])
    db_session.flush()
    spec_id = spec.id
    model_id = model.id
    db_session.commit()
    return spec_id, model_id


def findings_text(note: str) -> str:
    """Return deterministic findings text."""
    return (
        f"- Clarity: PASS — {note}\n"
        "- Measurability: FAIL — lacks threshold\n"
        "- Testability: PASS — testable\n"
        "- Atomicity: PASS — one behavior\n"
        "- Ambiguity-free: PASS — no ambiguity"
    )


@pytest.mark.asyncio
async def test_inspection_api_persists_and_lists_newest_first(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Inspection API persists rows and lists them newest-first."""
    spec_id, model_id = seed_spec_and_model(db_session)
    use_db_session(api_app, db_session)

    async def first_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult(findings_text("first"), 5, 6))

    async def second_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult(findings_text("second"), 5, 6))

    transport = ASGITransport(app=api_app)
    api_app.dependency_overrides[get_gateway_factory] = first_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})

    api_app.dependency_overrides[get_gateway_factory] = second_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        second = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})
        listed = await client.get(f"/api/specs/{spec_id}/inspections")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["findings"]["criteria"][0]["note"] == "second"
    assert [item["id"] for item in listed.json()] == [second.json()["id"], first.json()["id"]]


@pytest.mark.asyncio
async def test_inspection_api_missing_spec_and_model_conflicts(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Inspection API returns 404 for missing Spec and 409 for model conflicts."""
    spec_id, disabled_model_id = seed_spec_and_model(db_session, enabled=0)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_spec = await client.post("/api/specs/999/inspect", json={"model_id": disabled_model_id})
        missing_list = await client.get("/api/specs/999/inspections")
        missing_model = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": 999})
        disabled_model = await client.post(
            f"/api/specs/{spec_id}/inspect",
            json={"model_id": disabled_model_id},
        )

    assert missing_spec.status_code == 404
    assert missing_list.status_code == 404
    assert missing_model.status_code == 409
    assert disabled_model.status_code == 409


@pytest.mark.asyncio
async def test_inspection_api_parser_empty_and_gateway_failure_write_no_rows(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Parser-empty maps to 422 and gateway failure maps to 502 with no inspection row."""
    spec_id, model_id = seed_spec_and_model(db_session)
    use_db_session(api_app, db_session)

    async def empty_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("No findings", 1, 1))

    api_app.dependency_overrides[get_gateway_factory] = empty_gateway_factory
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_response = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})

    assert empty_response.status_code == 422
    assert "No inspection criteria" in empty_response.json()["detail"]
    assert db_session.scalars(select(SpecInspection)).all() == []

    async def failing_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayError("down"))

    api_app.dependency_overrides[get_gateway_factory] = failing_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        failure_response = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})

    assert failure_response.status_code == 502
    assert db_session.scalars(select(SpecInspection)).all() == []
