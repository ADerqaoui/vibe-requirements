"""Cost service tests."""
from sqlalchemy.orm import Session

from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.services.cost_service import cost_summary, start_of_month_utc


def test_cost_summary_aggregates_successful_paid_spend(db_session: Session) -> None:
    """Cost summary uses successful rows and excludes zero-cost models from breakdowns."""
    openai_model = Model(
        provider="openai",
        name="gpt",
        api_model_id="gpt-test",
        tier="high",
        input_cost_per_1k=1,
        output_cost_per_1k=1,
        enabled=1,
    )
    anthropic_model = Model(
        provider="anthropic",
        name="claude",
        api_model_id="claude-test",
        tier="high",
        input_cost_per_1k=2,
        output_cost_per_1k=0,
        enabled=1,
    )
    free_model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add_all([openai_model, anthropic_model, free_model])
    db_session.flush()
    db_session.add_all([
        Setting(key="cost_ceiling_sek", value="10"),
        CallLog(
            task="manual",
            provider="openai",
            model_id=openai_model.id,
            cost_sek=4,
            status="success",
            created_at=start_of_month_utc(),
        ),
        CallLog(
            task="manual",
            provider="anthropic",
            model_id=anthropic_model.id,
            cost_sek=8,
            status="success",
            created_at=start_of_month_utc(),
        ),
        CallLog(
            task="manual",
            provider="openai",
            model_id=openai_model.id,
            cost_sek=10,
            status="failure",
            created_at=start_of_month_utc(),
        ),
        CallLog(
            task="manual",
            provider="openai",
            model_id=openai_model.id,
            cost_sek=7,
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

    summary = cost_summary(db_session)

    assert summary.currency == "SEK"
    assert summary.ceiling_sek == 10
    assert summary.month_spent_sek == 12
    assert summary.month_remaining_sek == 0
    assert summary.all_time_spent_sek == 19
    assert [item.model_dump() for item in summary.by_provider] == [
        {"provider": "anthropic", "month_sek": 8.0},
        {"provider": "openai", "month_sek": 4.0},
    ]
    assert [item.model_dump() for item in summary.by_model] == [
        {"model_id": openai_model.id, "model_name": "gpt", "month_sek": 4.0},
        {"model_id": anthropic_model.id, "model_name": "claude", "month_sek": 8.0},
    ]
