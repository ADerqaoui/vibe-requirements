"""Inspector service tests."""
import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.gateway.base import GatewayError, GatewayResult
from app.inspector.parser import ParseFindingsError
from app.models.call_log import CallLog
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.models.prompt import Prompt
from app.models.setting import Setting
from app.seed.run import seed_prompts
from app.services.gateway_service import GatewayRuntime
from app.services.inspector_service import (
    InspectorModelUnavailableError,
    get_enabled_inspector_model,
    inspect_spec,
    resolve_inspector_model,
)


class FakeGateway:
    """Fake inspector gateway."""

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


def seed_spec_and_model(db_session: Session, enabled: int = 1) -> tuple[int, Model]:
    """Seed one Spec and one model."""
    seed_prompts(db_session)
    project = Project(name="Demo")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="The system shall brake.", source="ai")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=enabled)
    db_session.add_all([spec, model])
    db_session.flush()
    spec_id = spec.id
    db_session.commit()
    return spec_id, model


@pytest.mark.asyncio
async def test_inspector_service_persists_parsed_findings(db_session: Session) -> None:
    """A successful fake gateway call persists parsed findings JSON."""
    spec_id, model = seed_spec_and_model(db_session)
    gateway = FakeGateway(
        GatewayResult(
            "- Clarity: PASS — clear\n"
            "- Measurability: FAIL — lacks threshold\n"
            "- Testability: PASS — testable\n"
            "- Atomicity: PASS — one thing\n"
            "- Ambiguity-free: FAIL — says quickly\n"
            "Overall needs measurable threshold.",
            20,
            10,
        )
    )

    row = await inspect_spec(
        db=db_session,
        spec_id=spec_id,
        model=model,
        gateway=gateway,
        runtime=GatewayRuntime(retry_count=0),
    )

    persisted = db_session.get(SpecInspection, row.id)
    assert persisted is not None
    findings = json.loads(persisted.findings)
    assert findings["criteria"][1] == {
        "name": "Measurability",
        "verdict": "FAIL",
        "note": "lacks threshold",
    }
    assert findings["summary"] == "Overall needs measurable threshold."
    assert persisted.summary == "Overall needs measurable threshold."
    assert persisted.passes == 1


@pytest.mark.asyncio
async def test_inspector_service_gateway_failure_writes_no_inspection(db_session: Session) -> None:
    """Gateway failure propagates and does not persist an inspection row."""
    spec_id, model = seed_spec_and_model(db_session)

    with pytest.raises(GatewayError):
        await inspect_spec(
            db=db_session,
            spec_id=spec_id,
            model=model,
            gateway=FakeGateway(GatewayError("down")),
            runtime=GatewayRuntime(retry_count=0),
        )

    assert db_session.scalars(select(SpecInspection)).all() == []
    assert db_session.scalars(select(CallLog)).one().status == "failure"


@pytest.mark.asyncio
async def test_inspector_service_parser_empty_writes_no_inspection(db_session: Session) -> None:
    """Parser-empty failure logs the call but writes no inspection row."""
    spec_id, model = seed_spec_and_model(db_session)

    with pytest.raises(ParseFindingsError):
        await inspect_spec(
            db=db_session,
            spec_id=spec_id,
            model=model,
            gateway=FakeGateway(GatewayResult("No criteria here", 1, 1)),
            runtime=GatewayRuntime(retry_count=0),
        )

    assert db_session.scalars(select(SpecInspection)).all() == []
    assert db_session.scalars(select(CallLog)).one().status == "success"


def test_inspector_service_rejects_missing_or_disabled_model_before_call(
    db_session: Session,
) -> None:
    """Model validation raises before callers build or invoke a gateway."""
    _spec_id, disabled_model = seed_spec_and_model(db_session, enabled=0)

    with pytest.raises(InspectorModelUnavailableError, match="Model not found"):
        get_enabled_inspector_model(db_session, 999)
    with pytest.raises(InspectorModelUnavailableError, match="Model is disabled"):
        get_enabled_inspector_model(db_session, disabled_model.id)


def test_resolve_inspector_model_router_ignores_supplied_model_id(db_session: Session) -> None:
    """Router-on inspection selects high tier and ignores manual input."""
    _spec_id, manual = seed_spec_and_model(db_session)
    routed = Model(provider="ollama", name="high", ollama_tag="high", tier="high", enabled=1)
    db_session.add_all([routed, Setting(key="router_enabled", value="true")])
    db_session.commit()

    selected = resolve_inspector_model(db_session, manual.id)

    assert selected.id == routed.id


def test_resolve_inspector_model_manual_requires_model_id(db_session: Session) -> None:
    """Router-off inspection requires a supplied model id."""
    with pytest.raises(InspectorModelUnavailableError, match="Model is required"):
        resolve_inspector_model(db_session, None)


@pytest.mark.asyncio
async def test_inspector_service_passes_spec_layer_to_render(db_session: Session) -> None:
    """Inspector render receives the Spec layer id."""
    spec_id, model = seed_spec_and_model(db_session)
    spec = db_session.get(Spec, spec_id)
    assert spec is not None
    prompt = Prompt(
        task="inspect_spec",
        name="Layer inspect",
        layer_id=spec.layer_id,
        version=1,
        enabled=1,
        template="Layer inspect {spec_statement}",
    )
    db_session.add(prompt)
    db_session.commit()

    await inspect_spec(
        db=db_session,
        spec_id=spec_id,
        model=model,
        gateway=FakeGateway(
            GatewayResult(
                "- Clarity: PASS — clear\n"
                "- Measurability: PASS — measurable\n"
                "- Testability: PASS — testable\n"
                "- Atomicity: PASS — one thing\n"
                "- Ambiguity-free: PASS — precise",
                10,
                5,
            )
        ),
        runtime=GatewayRuntime(retry_count=0),
    )

    log = db_session.scalars(select(CallLog)).one()
    assert log.prompt_id == prompt.id
