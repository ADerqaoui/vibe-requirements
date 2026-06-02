"""Gateway service tests."""
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.gateway.base import CostCeilingExceededError, GatewayError, GatewayResult
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.services.gateway_service import GatewayRuntime, complete_model


class FakeGateway:
    """Fake gateway returning or raising a configured outcome."""

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


@pytest.mark.asyncio
async def test_service_allows_paid_model_below_ceiling(db_session: Session) -> None:
    """Paid calls proceed when current-month spend is below the ceiling."""
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
        model,
        Setting(key="cost_ceiling_sek", value="5"),
        Setting(key="fx_rate_usd_sek", value="10"),
    ])
    db_session.commit()
    db_session.refresh(model)
    gateway = FakeGateway(GatewayResult(text="done", in_tokens=10, out_tokens=10))

    result = await complete_model(
        db=db_session,
        model=model,
        gateway=gateway,
        prompt="hello",
        system=None,
        runtime=GatewayRuntime(retry_count=0),
    )

    assert result.text == "done"
    assert gateway.calls == 1
    assert db_session.scalars(select(CallLog)).one().status == "success"


@pytest.mark.asyncio
async def test_service_blocks_paid_model_at_ceiling_before_gateway(db_session: Session) -> None:
    """Ceiling blocks paid calls before gateway execution and logging."""
    model = Model(
        provider="openai",
        name="gpt",
        api_model_id="gpt-test",
        tier="high",
        input_cost_per_1k=1,
        output_cost_per_1k=0,
        enabled=1,
    )
    db_session.add_all([
        model,
        Setting(key="cost_ceiling_sek", value="5"),
        CallLog(task="manual", provider="openai", cost_sek=5, status="success"),
    ])
    db_session.commit()
    db_session.refresh(model)
    gateway = FakeGateway(GatewayResult(text="blocked", in_tokens=1, out_tokens=1))

    with pytest.raises(CostCeilingExceededError) as raised:
        await complete_model(
            db=db_session,
            model=model,
            gateway=gateway,
            prompt="hello",
            system=None,
            runtime=GatewayRuntime(retry_count=0),
        )

    assert raised.value.spent_sek == 5
    assert raised.value.ceiling_sek == 5
    assert gateway.calls == 0
    assert len(db_session.scalars(select(CallLog)).all()) == 1


@pytest.mark.asyncio
async def test_service_allows_free_model_even_when_over_ceiling(db_session: Session) -> None:
    """Free model calls are never blocked by spend."""
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add_all([
        model,
        Setting(key="cost_ceiling_sek", value="0"),
        CallLog(task="manual", provider="openai", cost_sek=100, status="success"),
    ])
    db_session.commit()
    db_session.refresh(model)
    gateway = FakeGateway(GatewayResult(text="free", in_tokens=1, out_tokens=1))

    result = await complete_model(
        db=db_session,
        model=model,
        gateway=gateway,
        prompt="hello",
        system=None,
        runtime=GatewayRuntime(retry_count=0),
    )

    assert result.text == "free"
    assert gateway.calls == 1
    assert len(db_session.scalars(select(CallLog)).all()) == 2


@pytest.mark.asyncio
async def test_service_zero_ceiling_blocks_paid_but_failed_spend_does_not_count(
    db_session: Session,
) -> None:
    """A zero ceiling blocks paid calls, and historical failures do not count."""
    model = Model(
        provider="openai",
        name="gpt",
        api_model_id="gpt-test",
        tier="high",
        input_cost_per_1k=0,
        output_cost_per_1k=1,
        enabled=1,
    )
    db_session.add_all([
        model,
        Setting(key="cost_ceiling_sek", value="10"),
        CallLog(task="manual", provider="openai", cost_sek=99, status="failure"),
    ])
    db_session.commit()
    db_session.refresh(model)

    allowed_gateway = FakeGateway(GatewayResult(text="allowed", in_tokens=1, out_tokens=1))
    await complete_model(
        db=db_session,
        model=model,
        gateway=allowed_gateway,
        prompt="hello",
        system=None,
        runtime=GatewayRuntime(retry_count=0),
    )
    db_session.get(Setting, "cost_ceiling_sek").value = "0"
    db_session.commit()
    blocked_gateway = FakeGateway(GatewayResult(text="blocked", in_tokens=1, out_tokens=1))

    with pytest.raises(CostCeilingExceededError):
        await complete_model(
            db=db_session,
            model=model,
            gateway=blocked_gateway,
            prompt="hello",
            system=None,
            runtime=GatewayRuntime(retry_count=0),
        )

    assert allowed_gateway.calls == 1
    assert blocked_gateway.calls == 0
