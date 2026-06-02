"""Spec-parent generation API tests."""
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
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.models.call_log import CallLog
from app.seed.run import seed_prompts


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
    """Seed a Spec parent and generation model."""
    Model.__table__
    Prompt.__table__
    seed_prompts(db_session)
    project = Project(name="Demo")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Brake safely", source="ai")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=enabled)
    db_session.add_all([spec, model])
    db_session.flush()
    spec_id = spec.id
    model_id = model.id
    db_session.commit()
    return spec_id, model_id


@pytest.mark.asyncio
async def test_spec_generation_api_returns_candidates(api_app: FastAPI, db_session: Session) -> None:
    """Spec generation API returns parsed candidates through the fake gateway."""
    spec_id, model_id = seed_spec_and_model(db_session)
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("1. Child\n2. Trace", 5, 6))

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": model_id, "count": 2},
        )

    assert response.status_code == 200
    assert response.json()["candidates"] == [
        {"index": 1, "statement": "Child"},
        {"index": 2, "statement": "Trace"},
    ]
    log = db_session.scalars(select(CallLog)).one()
    prompt = db_session.query(Prompt).filter_by(task="generate_spec_to_child", version=1).one()
    assert log.prompt_id == prompt.id
    assert log.prompt_version == prompt.version


@pytest.mark.asyncio
async def test_spec_generation_api_missing_spec_model_disabled_and_count(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Spec generation API returns requested 404, 409, and 422 paths."""
    spec_id, disabled_model_id = seed_spec_and_model(db_session, enabled=0)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_spec = await client.post(
            "/api/specs/999/generate",
            json={"model_id": disabled_model_id, "count": 1},
        )
        missing_model = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": 999, "count": 1},
        )
        disabled_model = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": disabled_model_id, "count": 1},
        )
        invalid_count = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": disabled_model_id, "count": 11},
        )

    assert missing_spec.status_code == 404
    assert missing_model.status_code == 409
    assert disabled_model.status_code == 409
    assert invalid_count.status_code == 422


@pytest.mark.asyncio
async def test_spec_generation_api_parser_empty_and_gateway_failure(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Parser empty maps to 422 and gateway failure maps to 502."""
    spec_id, model_id = seed_spec_and_model(db_session)
    use_db_session(api_app, db_session)

    async def empty_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("Specifications:", 1, 1))

    api_app.dependency_overrides[get_gateway_factory] = empty_gateway_factory
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_response = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": model_id, "count": 2},
        )

    async def failing_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayError("down"))

    api_app.dependency_overrides[get_gateway_factory] = failing_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        failure_response = await client.post(
            f"/api/specs/{spec_id}/generate",
            json={"model_id": model_id, "count": 2},
        )

    assert empty_response.status_code == 422
    assert failure_response.status_code == 502
