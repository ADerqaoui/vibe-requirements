"""Generation service layer-aware tests."""
import pytest
from sqlalchemy.orm import Session

from app.gateway.base import GatewayResult
from app.models.call_log import CallLog
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.seed.run import seed_prompts, seed_reference_data
from app.services.generation_service import GenerationRuntime, generate_for_parent


class FakeGateway:
    """Fake generation gateway."""

    async def health_check(self, timeout_seconds: float) -> None:
        """Always healthy."""

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Return one configured candidate."""
        return GatewayResult("1. Brake", 10, 8)


def seed_generation_parent(db_session: Session) -> tuple[int, Model]:
    """Seed a Spec parent for layer-aware generation tests."""
    seed_reference_data(db_session)
    seed_prompts(db_session)
    project = Project(name="Demo")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    layer = db_session.query(Layer).filter_by(name="System Requirement").one()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Stop safely", source="ai")
    db_session.add_all([spec, model])
    db_session.flush()
    parent_id = spec.id
    db_session.commit()
    return parent_id, model


@pytest.mark.asyncio
async def test_generation_service_passes_target_layer_to_render(db_session: Session) -> None:
    """Layer-specific generation prompts are selected for the target layer."""
    parent_id, model = seed_generation_parent(db_session)
    target_id = db_session.query(Layer).filter_by(name="System Architecture").one().id
    db_session.add(
        Prompt(
            task="generate_spec_to_child",
            name="Layer prompt",
            layer_id=target_id,
            version=1,
            enabled=1,
            template="Layer prompt {parent_statement} {count}",
        )
    )
    db_session.commit()

    await generate_for_parent(
        db=db_session,
        parent_kind="spec",
        parent_id=parent_id,
        model=model,
        gateway=FakeGateway(),
        count=1,
        runtime=GenerationRuntime(retry_count=0),
        target_layer_id=target_id,
    )

    log = db_session.query(CallLog).order_by(CallLog.id.desc()).first()
    assert log is not None
    assert log.rendered_prompt == "Layer prompt Stop safely 1"
