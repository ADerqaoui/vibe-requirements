"""Inspection API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayError, GatewayResult
from app.models.call_log import CallLog
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.setting import Setting
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.seed.run import seed_prompts


class FakeGateway:
    """API fake gateway."""

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


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def seed_spec_and_model(db_session: Session, enabled: int = 1) -> tuple[int, int]:
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
    model_id = model.id
    db_session.commit()
    return spec_id, model_id


def findings_text(note: str) -> str:
    """Return deterministic findings text."""
    return (
        f"- Clarity: PASS — {note}\n"
        "- Measurability: FAIL — lacks threshold\n"
        "- Testability: PASS — testable\n"
        "- Atomicity: PASS — one behavior\n"
        "- Ambiguity-free: PASS — no ambiguity\n"
        f"Summary for {note}"
    )


@pytest.mark.asyncio
async def test_inspection_api_persists_and_lists_newest_first(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Inspection API persists rows and lists them newest-first."""
    spec_id, model_id = seed_spec_and_model(db_session)
    prompt = Prompt(task="inspect_spec", name="EARS", version=1, enabled=1, template="Explicit {spec_statement}")
    db_session.add(prompt)
    db_session.commit()
    use_db_session(api_app, db_session)

    async def first_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult(findings_text("first"), 5, 6))

    async def second_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult(findings_text("second"), 5, 6))

    transport = ASGITransport(app=api_app)
    api_app.dependency_overrides[get_gateway_factory] = first_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id, "prompt_id": prompt.id})

    api_app.dependency_overrides[get_gateway_factory] = second_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        second = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id, "prompt_id": prompt.id})

    first_row = db_session.get(SpecInspection, first.json()["id"])
    second_row = db_session.get(SpecInspection, second.json()["id"])
    assert first_row is not None
    assert second_row is not None
    first_row.created_at = "2030-01-01T00:00:00"
    second_row.created_at = "2020-01-01T00:00:00"
    db_session.commit()

    need_id = db_session.get(Spec, spec_id).need_id
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get(f"/api/specs/{spec_id}/inspections")
        spec_tree = await client.get(f"/api/needs/{need_id}/spec-tree")

    assert first.status_code == 200
    assert second.status_code == 200
    response_keys = {
        "id",
        "spec_id",
        "model_id",
        "selected_model_id",
        "selected_model_name",
        "selected_prompt_id",
        "selected_prompt_name",
        "findings",
        "summary",
        "passes",
        "created_at",
    }
    assert set(first.json().keys()) == response_keys
    assert set(listed.json()[0].keys()) == response_keys
    assert second.json()["findings"]["criteria"][0]["note"] == "second"
    assert first.json()["summary"] == "Summary for first"
    assert listed.json()[0]["summary"] == first_row.summary
    assert [item["id"] for item in listed.json()] == [first.json()["id"], second.json()["id"]]
    assert spec_tree.json()[0]["latest_inspection_id"] == listed.json()[0]["id"]
    logs = db_session.scalars(select(CallLog).order_by(CallLog.id)).all()
    assert {log.prompt_id for log in logs} == {prompt.id}
    assert {log.prompt_version for log in logs} == {prompt.version}
    assert first.json()["selected_prompt_id"] == prompt.id
    assert first.json()["selected_prompt_name"] == "EARS"


@pytest.mark.asyncio
async def test_inspection_api_router_on_ignores_model_id_and_reports_selected_model(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Router-on inspection can omit model_id and reports the selected model."""
    spec_id, manual_model_id = seed_spec_and_model(db_session)
    routed = Model(provider="ollama", name="high-router", ollama_tag="high-router", tier="high", enabled=1)
    db_session.add_all([routed, Setting(key="router_enabled", value="true")])
    db_session.commit()
    use_db_session(api_app, db_session)
    selected_ids: list[int] = []

    async def override_gateway_factory():
        def factory(model, _settings):
            selected_ids.append(model.id)
            return FakeGateway(GatewayResult(findings_text("router"), 5, 6))

        return factory

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/specs/{spec_id}/inspect", json={})
        ignored = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": manual_model_id})

    assert response.status_code == 200
    assert response.json()["selected_model_id"] == routed.id
    assert response.json()["selected_model_name"] == "high-router"
    assert ignored.status_code == 200
    assert selected_ids == [routed.id, routed.id]


@pytest.mark.asyncio
async def test_inspection_api_missing_spec_and_model_conflicts(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Inspection API returns 404 for missing Spec and 409 for model conflicts."""
    spec_id, disabled_model_id = seed_spec_and_model(db_session, enabled=0)
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing_spec = await client.post("/api/specs/999/inspect", json={"model_id": disabled_model_id})
        missing_list = await client.get("/api/specs/999/inspections")
        missing_model = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": 999})
        disabled_model = await client.post(
            f"/api/specs/{spec_id}/inspect",
            json={"model_id": disabled_model_id},
        )
        missing_required_model = await client.post(f"/api/specs/{spec_id}/inspect", json={})

    assert missing_spec.status_code == 404
    assert missing_list.status_code == 404
    assert missing_model.status_code == 409
    assert disabled_model.status_code == 409
    assert missing_required_model.status_code == 400


@pytest.mark.asyncio
async def test_inspection_api_parser_empty_and_gateway_failure_write_no_rows(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Parser-empty maps to 422 and gateway failure maps to 502 with no inspection row."""
    spec_id, model_id = seed_spec_and_model(db_session)
    use_db_session(api_app, db_session)

    async def empty_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayResult("No findings", 1, 1))

    api_app.dependency_overrides[get_gateway_factory] = empty_gateway_factory
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_response = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})

    assert empty_response.status_code == 422
    assert "No inspection criteria" in empty_response.json()["detail"]
    assert db_session.scalars(select(SpecInspection)).all() == []

    async def failing_gateway_factory():
        return lambda _model, _settings: FakeGateway(GatewayError("down"))

    api_app.dependency_overrides[get_gateway_factory] = failing_gateway_factory
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        failure_response = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})

    assert failure_response.status_code == 502
    assert db_session.scalars(select(SpecInspection)).all() == []


@pytest.mark.asyncio
async def test_inspection_api_cost_ceiling_returns_402(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Inspection returns the structured 402 body when a paid model is blocked."""
    spec_id, model_id = seed_spec_and_model(db_session)
    model = db_session.get(Model, model_id)
    assert model is not None
    model.provider = "openai"
    model.api_model_id = "gpt-test"
    model.ollama_tag = None
    model.input_cost_per_1k = 1
    db_session.add_all([
        Setting(key="cost_ceiling_sek", value="2"),
        CallLog(task="manual", provider="openai", cost_sek=3, status="success"),
    ])
    db_session.commit()
    use_db_session(api_app, db_session)
    fake_gateway = FakeGateway(GatewayResult(findings_text("blocked"), 1, 1))

    async def override_gateway_factory():
        return lambda _model, _settings: fake_gateway

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id})

    assert response.status_code == 402
    assert response.json()["error"] == "cost_ceiling_exceeded"
    assert response.json()["spent_sek"] == 3
    assert response.json()["ceiling_sek"] == 2
    assert fake_gateway.calls == 0
