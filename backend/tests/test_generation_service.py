"""Generation service tests."""
import pytest
from sqlalchemy.orm import Session

from app.gateway.base import GatewayError, GatewayResult
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.models.layer import Layer
from app.services.generation_service import GenerationRuntime, ParentKind, generate_for_parent


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


def seed_generation_parent(db_session: Session, parent_kind: ParentKind) -> tuple[int, Model]:
    """Seed a Need or Spec parent for generation service tests."""
    project = Project(name="Demo")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    if parent_kind == "need":
        db_session.add(model)
        db_session.commit()
        return need.id, model
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add(layer)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Stop safely", source="ai")
    db_session.add_all([spec, model])
    db_session.flush()
    parent_id = spec.id
    db_session.commit()
    return parent_id, model


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_kind", ["need", "spec"])
async def test_generation_service_parses_fake_gateway_response(
    db_session: Session,
    parent_kind: ParentKind,
) -> None:
    """Service builds a prompt, logs through gateway service, and parses candidates."""
    parent_id, model = seed_generation_parent(db_session, parent_kind)

    result = await generate_for_parent(
        db=db_session,
        parent_kind=parent_kind,
        parent_id=parent_id,
        model=model,
        gateway=FakeGateway(GatewayResult("1. Brake\n2. Alert", 10, 8)),
        count=2,
        runtime=GenerationRuntime(retry_count=0),
    )

    assert [candidate.statement for candidate in result.candidates] == ["Brake", "Alert"]


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_kind", ["need", "spec"])
async def test_generation_service_parser_empty_propagates(
    db_session: Session,
    parent_kind: ParentKind,
) -> None:
    """Parser-empty failures propagate cleanly."""
    parent_id, model = seed_generation_parent(db_session, parent_kind)

    with pytest.raises(Exception, match="No specification candidates"):
        await generate_for_parent(
            db=db_session,
            parent_kind=parent_kind,
            parent_id=parent_id,
            model=model,
            gateway=FakeGateway(GatewayResult("Specifications:", 1, 1)),
            count=2,
            runtime=GenerationRuntime(retry_count=0),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_kind", ["need", "spec"])
async def test_generation_service_gateway_failure_propagates(
    db_session: Session,
    parent_kind: ParentKind,
) -> None:
    """Gateway failures are not hidden by generation parsing."""
    parent_id, model = seed_generation_parent(db_session, parent_kind)

    with pytest.raises(GatewayError, match="down"):
        await generate_for_parent(
            db=db_session,
            parent_kind=parent_kind,
            parent_id=parent_id,
            model=model,
            gateway=FakeGateway(GatewayError("down")),
            count=2,
            runtime=GenerationRuntime(retry_count=0),
        )
