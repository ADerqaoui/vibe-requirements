"""Shared prompt preview API test helpers."""
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayResult
from app.models.model import Model
from app.models.setting import Setting


class FakeGateway:
    """API fake gateway."""

    def __init__(self, outcome: GatewayResult):
        self.outcome = outcome
        self.calls = 0
        self.prompts: list[str] = []

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
        self.prompts.append(prompt)
        return self.outcome


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def use_gateway(api_app: FastAPI, gateway: FakeGateway) -> None:
    """Use a fake gateway in API requests."""

    async def override_gateway_factory():
        return lambda _model, _settings: gateway

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory


def add_model(db_session: Session, *, name: str = "gpt", tier: str = "high") -> Model:
    """Create one enabled paid model."""
    model = Model(
        provider="openai",
        name=name,
        api_model_id=f"{name}-test",
        tier=tier,
        input_cost_per_1k=2,
        output_cost_per_1k=4,
        enabled=1,
    )
    db_session.add(model)
    if db_session.get(Setting, "fx_rate_usd_sek") is None:
        db_session.add(Setting(key="fx_rate_usd_sek", value="10"))
    db_session.commit()
    db_session.refresh(model)
    return model
