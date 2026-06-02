"""Gateway service tests."""
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.gateway.base import GatewayError, GatewayResult
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.services.gateway_service import GatewayRuntime, complete_model


class FakeGateway:
    """Fake gateway returning or raising a configured outcome."""

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


@pytest.mark.asyncio
async def test_service_logs_success_with_frozen_cost_and_fx(db_session: Session) -> None:
    """Successful calls persist frozen cost and FX values."""
    model = Model(
        provider="openai",
        name="gpt",
        api_model_id="gpt-test",
        tier="high",
        input_cost_per_1k=2,
        output_cost_per_1k=4,
        enabled=1,
    )
    db_session.add_all([model, Setting(key="fx_rate_usd_sek", value="10")])
    db_session.commit()
    db_session.refresh(model)
    gateway = FakeGateway(GatewayResult(text="done", in_tokens=500, out_tokens=250))

    result = await complete_model(
        db=db_session,
        model=model,
        gateway=gateway,
        prompt="hello",
        system="system",
        runtime=GatewayRuntime(),
    )
    model.input_cost_per_1k = 99
    db_session.commit()

    log = db_session.scalars(select(CallLog)).one()
    assert result.cost_sek == 20
    assert log.cost_sek == 20
    assert log.fx_rate == 10
    assert log.provider == "openai"
    assert log.status == "success"
    assert log.rendered_prompt == "System:\nsystem\n\nUser:\nhello"


@pytest.mark.asyncio
async def test_service_logs_failure(db_session: Session) -> None:
    """Failed gateway calls still persist a failure row."""
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    with pytest.raises(GatewayError):
        await complete_model(
            db=db_session,
            model=model,
            gateway=FakeGateway(GatewayError("down")),
            prompt="hello",
            system=None,
            runtime=GatewayRuntime(retry_count=0),
        )

    log = db_session.scalars(select(CallLog)).one()
    assert log.status == "failure"
    assert log.provider == "ollama"
    assert log.model_id == model.id
    assert log.rendered_prompt == "hello"
