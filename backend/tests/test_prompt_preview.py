"""Prompt preview API success tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.gateway.base import GatewayResult
from app.models.call_log import CallLog
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from prompt_preview_helpers import FakeGateway, add_model, use_db_session, use_gateway


@pytest.mark.asyncio
async def test_prompt_preview_returns_rendered_output_cost_and_logs(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Valid preview returns rendered output cost and writes a preview call log."""
    model = add_model(db_session)
    use_db_session(api_app, db_session)
    use_gateway(api_app, FakeGateway(GatewayResult("preview output", 500, 250)))

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/preview",
            json={
                "task": "classify_spec",
                "template": "Score {spec_statement}",
                "variables": {"spec_statement": "The system shall stop."},
                "model_id": model.id,
            },
        )
        summary_response = await client.get("/api/cost-summary")

    log = db_session.scalars(select(CallLog)).one()
    assert response.status_code == 200
    assert response.json() == {
        "rendered_prompt": "Score The system shall stop.",
        "output": "preview output",
        "model_id": model.id,
        "model_name": "gpt",
        "cost_sek": 20,
    }
    assert log.task == "preview"
    assert log.cost_sek == 20
    assert summary_response.json()["month_spent_sek"] == 20


@pytest.mark.asyncio
async def test_prompt_preview_does_not_create_specs_or_inspections(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Preview keeps structural tables unchanged."""
    model = add_model(db_session)
    before_specs = db_session.scalar(select(func.count(Spec.id)))
    before_inspections = db_session.scalar(select(func.count(SpecInspection.id)))
    use_db_session(api_app, db_session)
    use_gateway(api_app, FakeGateway(GatewayResult("preview output", 1, 1)))

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/preview",
            json={
                "task": "classify_spec",
                "template": "Score {spec_statement}",
                "variables": {"spec_statement": "Spec"},
                "model_id": model.id,
            },
        )

    assert response.status_code == 200
    assert db_session.scalar(select(func.count(Spec.id))) == before_specs
    assert db_session.scalar(select(func.count(SpecInspection.id))) == before_inspections


@pytest.mark.asyncio
async def test_prompt_preview_omitted_model_uses_routed_model(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Omitted model_id falls back to router selection for the task."""
    add_model(db_session, name="mid", tier="mid")
    routed_model = add_model(db_session, name="high", tier="high")
    gateway = FakeGateway(GatewayResult("routed", 1, 1))
    use_db_session(api_app, db_session)
    use_gateway(api_app, gateway)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/preview",
            json={
                "task": "inspect_spec",
                "template": "Inspect {spec_statement}",
                "variables": {"spec_statement": "Spec"},
            },
        )

    assert response.status_code == 200
    assert response.json()["model_id"] == routed_model.id
    assert response.json()["model_name"] == "high"


@pytest.mark.asyncio
async def test_prompt_contracts_endpoint(api_app: FastAPI) -> None:
    """Contracts endpoint returns required variables by task."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/prompts/contracts")

    assert response.status_code == 200
    assert response.json() == {
        "generate_need_to_spec": ["count", "parent_statement"],
        "generate_spec_to_child": ["count", "parent_statement"],
        "classify_spec": ["spec_statement"],
        "inspect_spec": ["spec_statement"],
    }
