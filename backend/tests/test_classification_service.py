"""Classification service tests."""
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.gateway.base import GatewayError, GatewayResult
from app.models.call_log import CallLog
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.seed.run import seed_prompts
from app.services.classification_service import (
    CLASSIFICATION_TAGS,
    ClassificationModelError,
    ClassificationRuntime,
    classify_spec_complexity,
)


class FakeGateway:
    """Fake gateway for one classification model."""

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


def seed_spec_and_models(db_session: Session, enabled: bool = True) -> tuple[Spec, list[Model]]:
    """Seed one Spec and the required classification model rows."""
    Model.__table__
    Prompt.__table__
    seed_prompts(db_session)
    project = Project(name="Demo")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Need")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Spec text", source="ai")
    models = [
        Model(
            provider="ollama",
            name=tag,
            ollama_tag=tag,
            tier="mid",
            enabled=1 if enabled else 0,
        )
        for tag in CLASSIFICATION_TAGS
    ]
    db_session.add_all([spec, *models])
    db_session.commit()
    return spec, models


@pytest.mark.asyncio
async def test_classification_service_persists_median_and_logs(db_session: Session) -> None:
    """Three fake votes are logged and persisted as median complexity."""
    spec, models = seed_spec_and_models(db_session)
    outcomes = {
        models[0].id: GatewayResult("5", 1, 1),
        models[1].id: GatewayResult("2", 1, 1),
        models[2].id: GatewayResult("3", 1, 1),
    }
    call_order: list[int] = []

    def gateway_factory(model: Model, _settings: Settings) -> FakeGateway:
        call_order.append(model.id)
        return FakeGateway(outcomes[model.id])

    result = await classify_spec_complexity(
        db=db_session,
        spec=spec,
        gateway_factory=gateway_factory,
        settings=Settings(),
        runtime=ClassificationRuntime(retry_count=0),
    )

    logs = db_session.scalars(select(CallLog).order_by(CallLog.id)).all()
    assert result.complexity == 3
    assert [vote.vote for vote in result.votes] == [5, 2, 3]
    assert spec.complexity == 3
    assert call_order == [model.id for model in models]
    assert len(logs) == 3
    assert {log.status for log in logs} == {"success"}
    prompt = db_session.query(Prompt).filter_by(task="classify_spec", version=1).one()
    assert {log.prompt_id for log in logs} == {prompt.id}
    assert {log.prompt_version for log in logs} == {prompt.version}


@pytest.mark.asyncio
async def test_classification_service_missing_model_prevents_gateway_calls(
    db_session: Session,
) -> None:
    """Missing or disabled required models fail before gateway calls."""
    spec, _models = seed_spec_and_models(db_session, enabled=False)
    gateway_calls = 0

    def gateway_factory(_model: Model, _settings: Settings) -> FakeGateway:
        nonlocal gateway_calls
        gateway_calls += 1
        return FakeGateway(GatewayResult("3", 1, 1))

    with pytest.raises(ClassificationModelError, match="missing or disabled"):
        await classify_spec_complexity(
            db=db_session,
            spec=spec,
            gateway_factory=gateway_factory,
            settings=Settings(),
            runtime=ClassificationRuntime(retry_count=0),
        )

    assert gateway_calls == 0
    assert spec.complexity is None


@pytest.mark.asyncio
async def test_classification_service_passes_spec_layer_to_render(db_session: Session) -> None:
    """Classification render receives the Spec layer id."""
    spec, models = seed_spec_and_models(db_session)
    prompt = Prompt(
        task="classify_spec",
        name="Layer classify",
        layer_id=spec.layer_id,
        version=1,
        enabled=1,
        template="Layer classify {spec_statement}",
    )
    db_session.add(prompt)
    db_session.commit()

    def gateway_factory(_model: Model, _settings: Settings) -> FakeGateway:
        return FakeGateway(GatewayResult("3", 1, 1))

    await classify_spec_complexity(
        db=db_session,
        spec=spec,
        gateway_factory=gateway_factory,
        settings=Settings(),
        runtime=ClassificationRuntime(retry_count=0),
    )

    logs = db_session.scalars(select(CallLog)).all()
    assert len(logs) == len(models)
    assert {log.prompt_id for log in logs} == {prompt.id}
