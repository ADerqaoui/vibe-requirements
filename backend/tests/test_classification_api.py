"""Classification API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.config import Settings
from app.db import get_db
from app.gateway.base import GatewayError, GatewayResult
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.services.classification_service import CLASSIFICATION_TAGS


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


def seed_spec_and_models(db_session: Session, enabled: bool = True) -> tuple[int, list[int]]:
    """Seed one Spec and required classification models."""
    Model.__table__
    Prompt.__table__
    project = Project(name="Demo")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Need")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Spec text", source="ai")
    models = [
        Model(
            provider="ollama",
            name=tag,
            ollama_tag=tag,
            tier="mid",
            enabled=1 if enabled else 0,
        )
        for tag in CLASSIFICATION_TAGS
    ]
    db_session.add_all([spec, *models])
    db_session.flush()
    spec_id = spec.id
    model_ids = [model.id for model in models]
    db_session.commit()
    return spec_id, model_ids


@pytest.mark.asyncio
async def test_classification_api_returns_votes_and_complexity(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Classification API returns three votes and median complexity."""
    spec_id, model_ids = seed_spec_and_models(db_session)
    use_db_session(api_app, db_session)
    outcomes = {
        model_ids[0]: GatewayResult("1", 1, 1),
        model_ids[1]: GatewayResult("5", 1, 1),
        model_ids[2]: GatewayResult("4", 1, 1),
    }

    async def override_gateway_factory():
        return lambda model, _settings: FakeGateway(outcomes[model.id])

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/specs/{spec_id}/classify")

    assert response.status_code == 200
    assert response.json()["complexity"] == 4
    assert response.json()["votes"] == [
        {"model_id": model_ids[0], "vote": 1},
        {"model_id": model_ids[1], "vote": 5},
        {"model_id": model_ids[2], "vote": 4},
    ]


@pytest.mark.asyncio
async def test_classification_api_missing_spec_and_model_conflict(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Missing Spec is 404 and missing classification model is 409."""
    spec_id, _model_ids = seed_spec_and_models(db_session, enabled=False)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_spec = await client.post("/api/specs/999/classify")
        missing_model = await client.post(f"/api/specs/{spec_id}/classify")

    assert missing_spec.status_code == 404
    assert missing_model.status_code == 409
    assert "missing or disabled" in missing_model.json()["detail"]


@pytest.mark.asyncio
async def test_classification_api_gateway_failure_returns_502(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Any gateway failure maps to 502."""
    spec_id, model_ids = seed_spec_and_models(db_session)
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        def factory(model: Model, _settings: Settings) -> FakeGateway:
            if model.id == model_ids[1]:
                return FakeGateway(GatewayError("down"))
            return FakeGateway(GatewayResult("3", 1, 1))

        return factory

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/specs/{spec_id}/classify")

    spec = db_session.get(Spec, spec_id)
    assert response.status_code == 502
    assert "Gateway failure" in response.json()["detail"]
    assert spec is not None
    assert spec.complexity is None
