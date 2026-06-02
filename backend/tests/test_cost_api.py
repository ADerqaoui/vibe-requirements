"""Cost API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.services.cost_service import start_of_month_utc


@pytest.mark.asyncio
async def test_cost_summary_api_returns_documented_shape(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """GET /api/cost-summary returns monthly and all-time spend data."""
    openai_model = Model(
        provider="openai",
        name="gpt",
        api_model_id="gpt-test",
        tier="high",
        input_cost_per_1k=1,
        output_cost_per_1k=1,
        enabled=1,
    )
    free_model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add_all([openai_model, free_model])
    db_session.flush()
    db_session.add_all([
        Setting(key="cost_ceiling_sek", value="60"),
        CallLog(
            task="manual",
            provider="openai",
            model_id=openai_model.id,
            cost_sek=12.34,
            status="success",
            created_at=start_of_month_utc(),
        ),
        CallLog(
            task="manual",
            provider="openai",
            model_id=openai_model.id,
            cost_sek=5,
            status="failure",
            created_at=start_of_month_utc(),
        ),
        CallLog(
            task="manual",
            provider="openai",
            model_id=openai_model.id,
            cost_sek=5,
            status="success",
            created_at="2000-01-01T00:00:00+00:00",
        ),
        CallLog(
            task="manual",
            provider="ollama",
            model_id=free_model.id,
            cost_sek=0,
            status="success",
            created_at=start_of_month_utc(),
        ),
    ])
    db_session.commit()

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/cost-summary")

    assert response.status_code == 200
    assert response.json() == {
        "currency": "SEK",
        "ceiling_sek": 60,
        "month_spent_sek": 12.34,
        "month_remaining_sek": 47.66,
        "all_time_spent_sek": 17.34,
        "by_provider": [{"provider": "openai", "month_sek": 12.34}],
        "by_model": [
            {"model_id": openai_model.id, "model_name": "gpt", "month_sek": 12.34},
        ],
    }
