"""Generation API layer validation tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayResult
from app.models.layer import Layer
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.seed.run import seed_prompts, seed_reference_data


class FakeGateway:
    """API fake gateway."""

    def __init__(self, outcome: GatewayResult):
        self.outcome = outcome
        self.calls = 0

    async def health_check(self, timeout_seconds: float) -> None:
        """Always healthy."""

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Return the configured outcome."""
        self.calls += 1
        return self.outcome


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def seed_need_and_model(db_session: Session) -> tuple[int, int]:
    """Seed a Need and model for generation API tests."""
    seed_reference_data(db_session)
    seed_prompts(db_session)
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add_all([need, model])
    db_session.flush()
    need_id = need.id
    model_id = model.id
    db_session.commit()
    return need_id, model_id


def seed_spec_and_model(db_session: Session) -> tuple[int, int, int]:
    """Seed a Spec parent, model, and allowed child layer id."""
    need_id, model_id = seed_need_and_model(db_session)
    parent_layer = db_session.query(Layer).filter_by(name="System Requirement").one()
    target_layer = db_session.query(Layer).filter_by(name="System Architecture").one()
    spec = Spec(need_id=need_id, layer_id=parent_layer.id, text="Stop safely", source="ai")
    db_session.add(spec)
    db_session.flush()
    spec_id = spec.id
    db_session.commit()
    return spec_id, model_id, target_layer.id


@pytest.mark.asyncio
async def test_generation_api_rejects_disallowed_target_layer_before_gateway(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Disallowed target layers return 422 and create no call log."""
    need_id, model_id = seed_need_and_model(db_session)
    disallowed_layer = db_session.query(Layer).filter_by(name="SW Requirement").one()
    use_db_session(api_app, db_session)
    fake_gateway = FakeGateway(GatewayResult("1. Brake", 5, 6))

    async def override_gateway_factory():
        return lambda _model, _settings: fake_gateway

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "count": 1, "target_layer_id": disallowed_layer.id},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "layer_not_allowed_for_parent"
    assert fake_gateway.calls == 0
    assert db_session.scalars(select(CallLog)).all() == []


@pytest.mark.asyncio
async def test_generation_api_accepts_spec_target_layer(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Spec generation accepts an allowed target layer."""
    spec_id, model_id, target_layer_id = seed_spec_and_model(db_session)
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("1. Child", 5, 6))

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": model_id, "count": 1, "target_layer_id": target_layer_id},
        )

    assert response.status_code == 200
    assert response.json()["candidates"] == [{"index": 1, "statement": "Child"}]
