"""Generation API cost-ceiling tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayResult
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.setting import Setting
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


@pytest.mark.asyncio
async def test_generation_api_cost_ceiling_returns_402(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Generation returns the structured 402 body when a paid model is blocked."""
    project = Project(name="Demo")
    seed_reference_data(db_session)
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
        Setting(key="router_enabled", value="true"),
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
            json={"count": 1},
        )

    assert response.status_code == 402
    assert response.json()["error"] == "cost_ceiling_exceeded"
    assert response.json()["spent_sek"] == 5
    assert response.json()["ceiling_sek"] == 4
    assert fake_gateway.calls == 0
