"""Gateway API tests."""
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
    """Force API requests in this module through the assertion session."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_complete_api_returns_result_and_logs(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """API success path uses injected fake gateway and logs."""
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(model)
    db_session.flush()
    model_id = model.id
    db_session.commit()
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("ok", 5, 6))

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/models/{model_id}/complete", json={"prompt": "hello"})

    log = db_session.scalars(select(CallLog)).one()
    assert response.status_code == 200
    assert response.json()["text"] == "ok"
    assert response.json()["in_tokens"] == 5
    assert log.status == "success"
    assert log.cost_sek == 0


@pytest.mark.asyncio
async def test_complete_api_missing_and_disabled(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """API returns 404 for missing models and 409 for disabled models."""
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=0)
    db_session.add(model)
    db_session.flush()
    model_id = model.id
    db_session.commit()
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_response = await client.post("/api/models/999/complete", json={"prompt": "hello"})
        disabled_response = await client.post(
            f"/api/models/{model_id}/complete",
            json={"prompt": "hello"},
        )

    assert missing_response.status_code == 404
    assert disabled_response.status_code == 409


@pytest.mark.asyncio
async def test_complete_api_gateway_failure_returns_502_and_logs(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Gateway errors return a clear 502 and a failure log."""
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(model)
    db_session.flush()
    model_id = model.id
    db_session.commit()
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayError("adapter not implemented"))

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/models/{model_id}/complete", json={"prompt": "hello"})

    log = db_session.scalars(select(CallLog)).one()
    assert response.status_code == 502
    assert "adapter not implemented" in response.json()["detail"]
    assert log.status == "failure"
