"""Prompt preview API error tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.gateway.base import GatewayResult
from app.models.call_log import CallLog
from app.models.setting import Setting
from prompt_preview_helpers import FakeGateway, add_model, use_db_session, use_gateway


@pytest.mark.asyncio
async def test_prompt_preview_rejects_invalid_template(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Invalid templates return 422 before gateway execution."""
    model = add_model(db_session)
    gateway = FakeGateway(GatewayResult("unused", 1, 1))
    use_db_session(api_app, db_session)
    use_gateway(api_app, gateway)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/preview",
            json={"task": "classify_spec", "template": "No variable", "variables": {}, "model_id": model.id},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "prompt_template_invalid"
    assert "missing variables: spec_statement" in response.json()["reason"]
    assert gateway.calls == 0


@pytest.mark.asyncio
async def test_prompt_preview_rejects_missing_variable_value(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Missing or empty required variables return 422."""
    model = add_model(db_session)
    use_db_session(api_app, db_session)
    use_gateway(api_app, FakeGateway(GatewayResult("unused", 1, 1)))

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/prompts/preview",
            json={
                "task": "classify_spec",
                "template": "Score {spec_statement}",
                "variables": {"spec_statement": ""},
                "model_id": model.id,
            },
        )

    assert response.status_code == 422
    assert response.json()["reason"] == "missing variable value: spec_statement"


@pytest.mark.asyncio
async def test_prompt_preview_cost_ceiling_returns_402(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Paid previews use the standard cost ceiling response."""
    model = add_model(db_session)
    db_session.add_all([
        Setting(key="cost_ceiling_sek", value="4"),
        CallLog(task="manual", provider="openai", model_id=model.id, cost_sek=5, status="success"),
    ])
    db_session.commit()
    gateway = FakeGateway(GatewayResult("blocked", 1, 1))
    use_db_session(api_app, db_session)
    use_gateway(api_app, gateway)

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

    assert response.status_code == 402
    assert response.json() == {
        "error": "cost_ceiling_exceeded",
        "spent_sek": 5,
        "ceiling_sek": 4,
        "currency": "SEK",
    }
    assert gateway.calls == 0
