"""Generation service tests."""
import pytest
from sqlalchemy.orm import Session

from app.gateway.base import GatewayError, GatewayResult
from app.models.call_log import CallLog
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.services.blacklist_service import BlacklistService
from app.services.embedding_service import EMBEDDING_DIMENSIONS
from app.services.generation_service import GenerationRuntime, ParentKind, generate_for_parent
from app.seed.run import seed_prompts


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


class FakeEmbeddingService:
    """Embedding fake keyed by text."""

    def __init__(self, embeddings: dict[str, list[float]]):
        self.embeddings = embeddings

    async def embed(self, text_value: str) -> list[float]:
        """Return the configured embedding."""
        return self.embeddings[text_value]


def unit_vector(first: float, second: float = 0.0) -> list[float]:
    """Return a 768-dim vector using the first two axes."""
    return [first, second, *([0.0] * (EMBEDDING_DIMENSIONS - 2))]


def seed_generation_parent(db_session: Session, parent_kind: ParentKind) -> tuple[int, Model]:
    """Seed a Need or Spec parent for generation service tests."""
    seed_prompts(db_session)
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
    log = db_session.query(CallLog).order_by(CallLog.id.desc()).first()
    prompt = db_session.query(Prompt).filter_by(
        task="generate_need_to_spec" if parent_kind == "need" else "generate_spec_to_child",
        version=1,
    ).one()
    assert log is not None
    assert log.prompt_id == prompt.id
    assert log.prompt_version == prompt.version


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


@pytest.mark.asyncio
async def test_generation_service_filters_parsed_candidates_against_blacklist(
    db_session: Session,
) -> None:
    """Generation filters parsed candidates against the parent blacklist."""
    parent_id, model = seed_generation_parent(db_session, "need")
    fake_embedding_service = FakeEmbeddingService(
        {
            "Rejected brake": unit_vector(1),
            "Brake": unit_vector(1),
            "Alert": unit_vector(0, 1),
        }
    )
    blacklist_service = BlacklistService(db_session, fake_embedding_service)
    await blacklist_service.add_blacklist_entry("need", parent_id, "Rejected brake")

    result = await generate_for_parent(
        db=db_session,
        parent_kind="need",
        parent_id=parent_id,
        model=model,
        gateway=FakeGateway(GatewayResult("1. Brake\n2. Alert", 10, 8)),
        count=2,
        runtime=GenerationRuntime(retry_count=0),
        blacklist_service=blacklist_service,
    )

    assert [candidate.statement for candidate in result.candidates] == ["Alert"]
