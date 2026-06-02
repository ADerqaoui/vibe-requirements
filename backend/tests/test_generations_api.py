"""Generation API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayError, GatewayResult
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.setting import Setting
from app.seed.run import seed_prompts


class FakeGateway:
    """API fake gateway."""

    def __init__(self, outcome: GatewayResult | GatewayError):
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
        """Return or raise the configured outcome."""
        self.calls += 1
        if isinstance(self.outcome, GatewayError):
            raise self.outcome
        return self.outcome


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def seed_need_and_model(db_session: Session, enabled: int = 1) -> tuple[int, int]:
    """Seed a Need and model for generation API tests."""
    seed_prompts(db_session)
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=enabled)
    db_session.add_all([need, model])
    db_session.flush()
    need_id = need.id
    model_id = model.id
    db_session.commit()
    return need_id, model_id


@pytest.mark.asyncio
async def test_generation_api_returns_candidates_and_logs(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Generation API uses fake gateway and writes call log."""
    need_id, model_id = seed_need_and_model(db_session)
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("1. Brake\n2. Alert", 5, 6))

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "count": 2},
        )

    log = db_session.scalars(select(CallLog)).one()
    assert response.status_code == 200
    assert response.json()["candidates"] == [
        {"index": 1, "statement": "Brake"},
        {"index": 2, "statement": "Alert"},
    ]
    assert log.status == "success"
    prompt = db_session.query(Prompt).filter_by(task="generate_need_to_spec", version=1).one()
    assert log.prompt_id == prompt.id
    assert log.prompt_version == prompt.version


@pytest.mark.asyncio
async def test_generation_api_missing_need_model_disabled_and_count(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Generation API returns requested 404, 409, and 422 paths."""
    need_id, disabled_model_id = seed_need_and_model(db_session, enabled=0)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_need = await client.post(
            "/api/needs/999/generate",
            json={"model_id": disabled_model_id, "count": 1},
        )
        missing_model = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": 999, "count": 1},
        )
        disabled_model = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": disabled_model_id, "count": 1},
        )
        invalid_count = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": disabled_model_id, "count": 11},
        )

    assert missing_need.status_code == 404
    assert missing_model.status_code == 409
    assert disabled_model.status_code == 409
    assert invalid_count.status_code == 422


@pytest.mark.asyncio
async def test_generation_api_parser_empty_and_gateway_failure(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Parser empty maps to 422 and gateway failure maps to 502."""
    need_id, model_id = seed_need_and_model(db_session)
    use_db_session(api_app, db_session)

    async def empty_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("Specifications:", 1, 1))

    api_app.dependency_overrides[get_gateway_factory] = empty_gateway_factory
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "count": 2},
        )

    async def failing_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayError("down"))

    api_app.dependency_overrides[get_gateway_factory] = failing_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        failure_response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "count": 2},
        )

    assert empty_response.status_code == 422
    assert failure_response.status_code == 502


@pytest.mark.asyncio
async def test_generation_api_cost_ceiling_returns_402(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Generation returns the structured 402 body when a paid model is blocked."""
    project = Project(name="Demo")
    seed_prompts(db_session)
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    model = Model(
        provider="openai",
        name="gpt",
        api_model_id="gpt-test",
        tier="high",
        input_cost_per_1k=1,
        output_cost_per_1k=1,
        enabled=1,
    )
    db_session.add_all([
        need,
        model,
        Setting(key="cost_ceiling_sek", value="4"),
        CallLog(task="manual", provider="openai", cost_sek=5, status="success"),
    ])
    db_session.flush()
    need_id = need.id
    model_id = model.id
    db_session.commit()
    use_db_session(api_app, db_session)
    fake_gateway = FakeGateway(GatewayResult("1. Blocked", 1, 1))

    async def override_gateway_factory():
        return lambda _model, _settings: fake_gateway

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "count": 1},
        )

    assert response.status_code == 402
    assert response.json()["error"] == "cost_ceiling_exceeded"
    assert response.json()["spent_sek"] == 5
    assert response.json()["ceiling_sek"] == 4
    assert fake_gateway.calls == 0
