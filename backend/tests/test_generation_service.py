"""Generation service tests."""
import pytest
from sqlalchemy.orm import Session

from app.gateway.base import GatewayError, GatewayResult
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.services.generation_service import GenerationRuntime, generate_specs_for_need


class FakeGateway:
    """Fake generation gateway."""

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
async def test_generation_service_parses_fake_gateway_response(db_session: Session) -> None:
    """Service builds a prompt, logs through gateway service, and parses candidates."""
    project = Project(name="Demo")
    need = Need(project_id=1, statement="Stop safely")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(project)
    db_session.flush()
    need.project_id = project.id
    db_session.add_all([need, model])
    db_session.commit()

    result = await generate_specs_for_need(
        db=db_session,
        need=need,
        model=model,
        gateway=FakeGateway(GatewayResult("1. Brake\n2. Alert", 10, 8)),
        count=2,
        runtime=GenerationRuntime(retry_count=0),
    )

    assert [candidate.statement for candidate in result.candidates] == ["Brake", "Alert"]


@pytest.mark.asyncio
async def test_generation_service_parser_empty_propagates(db_session: Session) -> None:
    """Parser-empty failures propagate cleanly."""
    project = Project(name="Demo")
    need = Need(project_id=1, statement="Stop safely")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(project)
    db_session.flush()
    need.project_id = project.id
    db_session.add_all([need, model])
    db_session.commit()

    with pytest.raises(Exception, match="No specification candidates"):
        await generate_specs_for_need(
            db=db_session,
            need=need,
            model=model,
            gateway=FakeGateway(GatewayResult("Specifications:", 1, 1)),
            count=2,
            runtime=GenerationRuntime(retry_count=0),
        )


@pytest.mark.asyncio
async def test_generation_service_gateway_failure_propagates(db_session: Session) -> None:
    """Gateway failures are not hidden by generation parsing."""
    project = Project(name="Demo")
    need = Need(project_id=1, statement="Stop safely")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(project)
    db_session.flush()
    need.project_id = project.id
    db_session.add_all([need, model])
    db_session.commit()

    with pytest.raises(GatewayError, match="down"):
        await generate_specs_for_need(
            db=db_session,
            need=need,
            model=model,
            gateway=FakeGateway(GatewayError("down")),
            count=2,
            runtime=GenerationRuntime(retry_count=0),
        )
